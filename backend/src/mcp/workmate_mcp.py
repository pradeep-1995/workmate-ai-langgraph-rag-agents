
# backend/src/mcp/workmate_mcp.py

from datetime import datetime

from fastmcp import FastMCP

from backend.data.workmate_db import (
    get_connection,
    utc_now,
    init_db,
)

from backend.core.logging import get_logger


logger = get_logger(__name__)
mcp = FastMCP("WorkMate")


# Initialize SQLite database
init_db()


# ============================================================
# RAG TOOL
# ============================================================

@mcp.tool()
def rag_tool(query: str) -> dict:
    """
    Search the productivity PDF knowledge base and return
    the top reranked results with source and page metadata.

    Use for factual or conceptual questions about stored documents.
    """
    if not query or not query.strip():
        return {
            "success": False,
            "error": "Query cannot be empty.",
        }

    try:
        from backend.src.rag.retriever import get_retriever
        from backend.src.rag.reranker import reranker_documents

        retriever = get_retriever()

        # Step 1: Retrieve relevant documents
        retrieved_docs = retriever.invoke(query)

        if not retrieved_docs:
            logger.warning("No documents retrieved for query: %s", query)
            return {
                "success": True,
                "query": query,
                "count": 0,
                "context": [],
                "message": "No relevant information found in the knowledge base.",
            }

        # Step 2: Rerank retrieved documents
        ranked_docs = reranker_documents(
            query=query,
            documents=retrieved_docs,
            top_k=3,
        )

        if not ranked_docs:
            logger.warning("No documents returned after reranking: %s", query)
            return {
                "success": True,
                "query": query,
                "count": 0,
                "context": [],
                "message": "No relevant information found after reranking.",
            }

        # Step 3: Return grounded context and source metadata
        context = []

        for index, document in enumerate(ranked_docs, start=1):
            metadata = document.metadata or {}

            context.append({
                "rank": index,
                "source": str(metadata.get("source", "Unknown source")),
                "page": metadata.get("page"),
                "content": document.page_content,
            })

        logger.info(
            "RAG search completed | retrieved=%d | returned=%d",
            len(retrieved_docs),
            len(ranked_docs),
        )

        return {
            "success": True,
            "query": query,
            "count": len(context),
            "context": context,
        }

    except Exception:
        logger.exception("Productivity knowledge search failed")
        return {
            "success": False,
            "error": "Knowledge search failed. Please try again later.",
        }


# ============================================================
# TASK MANAGEMENT TOOLS
# ============================================================

# ======== CREATE TASKS ========
@mcp.tool()
def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = "",
) -> dict:
    """
    Create a task in SQLite.

    Priority: low, medium, or high.
    Due date: YYYY-MM-DD, or empty for no due date.
    """
    title = title.strip()
    description = description.strip()
    priority = priority.strip().lower()
    due_date = due_date.strip()

    if not title:
        return {
            "success": False,
            "error": "Task title cannot be empty.",
        }

    if priority not in ("low", "medium", "high"):
        return {
            "success": False,
            "error": "Priority must be low, medium, or high.",
        }

    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": "Due date must use YYYY-MM-DD format.",
            }

    now = utc_now()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (
                title, description, priority, due_date,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (title, description, priority, due_date or None, now, now),
        )

        task_id = cursor.lastrowid

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    logger.info("Created task id=%s", task_id)

    return {
        "success": True,
        "task": dict(row),
    }


# ======== LIST TASKS ========
@mcp.tool()
def list_tasks(status: str = "all") -> dict:
    """
    List tasks from SQLite.

    Status can be all, pending, or completed.
    """
    status = status.strip().lower()

    if status not in ("all", "pending", "completed"):
        return {
            "success": False,
            "error": "Status must be all, pending, or completed.",
        }

    with get_connection() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY id DESC
                """,
                (status,),
            ).fetchall()

    tasks = [dict(row) for row in rows]

    return {
        "success": True,
        "count": len(tasks),
        "tasks": tasks,
    }


# ======== UPDATE TASKS ========
@mcp.tool()
def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    priority: str = "",
    due_date: str = "",
) -> dict:
    """
    Update a task's title, description, priority, or due date.

    Use due_date='none' to clear an existing due date.
    """
    updates = {}

    if title.strip():
        updates["title"] = title.strip()

    if description.strip():
        updates["description"] = description.strip()

    if priority.strip():
        priority = priority.strip().lower()

        if priority not in ("low", "medium", "high"):
            return {
                "success": False,
                "error": "Priority must be low, medium, or high.",
            }

        updates["priority"] = priority

    if due_date.strip():
        due_date = due_date.strip()

        if due_date.lower() == "none":
            updates["due_date"] = None
        else:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "error": "Due date must use YYYY-MM-DD or 'none'.",
                }

            updates["due_date"] = due_date

    if not updates:
        return {
            "success": False,
            "error": "Provide at least one field to update.",
        }

    updates["updated_at"] = utc_now()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if existing is None:
            return {
                "success": False,
                "error": f"Task {task_id} was not found.",
            }

        assignments = ", ".join(
            f"{column} = ?" for column in updates
        )

        conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            (*updates.values(), task_id),
        )

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    logger.info("Updated task id=%s", task_id)

    return {
        "success": True,
        "task": dict(row),
    }


# ======== COMPLETE TASKS ========
@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Mark a task as completed."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET status = 'completed', updated_at = ?
            WHERE id = ?
            """,
            (utc_now(), task_id),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "error": f"Task {task_id} was not found.",
            }

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    logger.info("Completed task id=%s", task_id)

    return {
        "success": True,
        "task": dict(row),
    }


# ======== DELETE TASKS ========
@mcp.tool()
def delete_task(task_id: int, confirm: bool = False) -> dict:
    """
    Delete a task by ID.

    Requires confirm=True. Ask the user to confirm before deletion.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if row is None:
            return {
                "success": False,
                "error": f"Task {task_id} was not found.",
            }

        if not confirm:
            return {
                "success": False,
                "confirmation_required": True,
                "task": dict(row),
                "message": (
                    "Ask the user to confirm deletion before retrying."
                ),
            }

        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )

    logger.info("Deleted task id=%s", task_id)

    return {
        "success": True,
        "deleted_task_id": task_id,
        "message": "Task deleted.",
    }


# ============================================================
# MCP SERVER ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
