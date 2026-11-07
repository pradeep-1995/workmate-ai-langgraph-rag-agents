from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class WorkmateState(TypedDict):
    messages: Annotated[list, add_messages]
    user_request: str
    user_context: dict
    router_decision: dict
    approval_status: str