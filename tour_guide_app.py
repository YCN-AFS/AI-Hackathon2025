import streamlit as st
import json
from PIL import Image
import base64
from pathlib import Path
import os
from typing import Annotated, Literal, Optional, Callable
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema.runnable import Runnable, RunnableConfig
from langchain.schema.runnable.base import RunnableLambda
from langgraph.prebuilt import ToolNode, tools_condition
import uuid
import requests
from datetime import datetime, timedelta

# Thiết lập API keys
os.environ["GOOGLE_API_KEY"] = "AIzaSyBt4n2O89U7XKNM2LDwa0DSP5MI80yEwpA"
os.environ["TAVILY_API_KEY"] = "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"

# Định nghĩa các agent
class ToAccommodation_Agent(BaseModel):
    """Chuyên gia về nơi ở (khách sạn, homestay, resort...) ở Việt Nam."""
    main_location: str = Field(
        ...,
        description="Địa điểm chính mà người dùng muốn đặt nơi ở",
        example="Nha Trang"
    )
    expense: str = Field(
        ...,
        description="Số tiền mà người dùng có thể bỏ ra thuê nơi ở",
        example="Dưới 200.000 VNĐ"
    )
    option: str = Field(
        ...,
        description="Những lưu ý, mong muốn, yêu cầu phụ của người dùng",
        example="Gần biển"
    )

class ToDestination_Agent(BaseModel):
    """Chuyên gia về địa điểm du lịch nổi tiếng ở Việt Nam."""
    location: str = Field(
        ...,
        description="Địa điểm du lịch mà người dùng quan tâm",
        example="Đà Lạt"
    )
    duration: str = Field(
        ...,
        description="Thời gian dự kiến cho chuyến đi",
        example="3 ngày"
    )
    interests: str = Field(
        ...,
        description="Sở thích và mong muốn của người dùng",
        example="Thích thiên nhiên, chụp ảnh"
    )

class ToFood_Agent(BaseModel):
    """Chuyên gia về ẩm thực địa phương."""
    location: str = Field(
        ...,
        description="Địa điểm muốn tìm hiểu về ẩm thực",
        example="Hội An"
    )
    preferences: str = Field(
        ...,
        description="Sở thích ẩm thực của người dùng",
        example="Đồ hải sản, món truyền thống"
    )
    budget: str = Field(
        ...,
        description="Ngân sách cho bữa ăn",
        example="200.000/người"
    )
    allergy: str = Field(
        ...,
        description="Danh sách các món ăn dị ứng",
        example="Đậu phộng, hải sản"
    )

class ToTransaction_Agent(BaseModel):
    """Chuyên gia về giao dịch và thanh toán."""
    pass

# Định nghĩa các class từ notebook
class Preferences(BaseModel):
    name: Optional[str] = Field("Vô Danh", description="Tên người dùng")
    number_member: Optional[str] = Field("2", description="Tổng số thành viên trong nhóm")
    total_expense: Optional[str] = Field("2 triệu", description="Chi phí tổng mà người dùng có thể bỏ ra cho chuyến đi")

def update_dialog_stack(container: list[str], what: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if what is None:
        return container
    if what == "pop":
        return container[:-1]
    return container + [what]

# State Management
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    preferences: Preferences
    Recommended_Tour: dict
    dialog_state: Annotated[
        list[
            Literal[
                "Primary_Agent",
                "Accommodation_Agent",
                "Destination_Agent",
                "Food_Agent",
                "Transaction_Agent"
            ]
        ],
        update_dialog_stack,
    ]

# Các prompt mẫu cho từng agent
PRIMARY_PROMPT = """Bạn là một trợ lý du lịch thông minh, chuyên giúp người dùng lên lịch trình và sắp xếp thời gian chuyến đi.
📌 Chức năng chính của bạn là điều phối cuộc hội thoại cho các Agent chuyên môn khác dựa trên câu hỏi của người dùng.
❌ Bạn không tư vấn về lịch trình, nơi ở, phương tiện di chuyển, ăn uống hay các hoạt động khác.

💡 **Hướng dẫn quan trọng chung:**
- Trả lời ngắn gọn, dễ hiểu bằng tiếng Việt (người dùng không hiểu các ngôn ngữ khác).
- Xưng hô thân thiện: 'tôi' với 'bạn'.
- Nếu có công cụ phù hợp, hãy sử dụng công cụ đó để có thêm thông tin phù hợp.
- Sau khi trả lời xong câu hỏi, hãy hỏi: "Tôi có thể giúp gì thêm cho bạn?"

Thông tin về người dùng:
- Tên: {name}
- Số thành viên: {number_member}
- Ngân sách: {total_expense}

🚀 Hãy giúp người dùng có một chuyến đi tuyệt vời!"""

ACCOMMODATION_PROMPT = """Bạn là chuyên gia tư vấn về nơi ở du lịch tại Việt Nam. Hãy tư vấn dựa trên:
- Địa điểm: {location}
- Ngân sách: {budget}
- Số người: {number_member}
- Yêu cầu thêm: {requirements}

Hãy đề xuất ít nhất 3 lựa chọn phù hợp, mỗi lựa chọn bao gồm:
1. Tên và loại hình nơi ở
2. Vị trí và khoảng cách đến các điểm du lịch
3. Giá cả và các gói dịch vụ
4. Đánh giá ưu/nhược điểm
5. Lời khuyên khi đặt phòng"""

DESTINATION_PROMPT = """Bạn là chuyên gia tư vấn về địa điểm du lịch tại Việt Nam. Với thông tin:
- Địa điểm: {location}
- Thời gian: {duration}
- Số người: {number_member}
- Ngân sách: {budget}
- Sở thích: {interests}

Hãy tư vấn chi tiết về:
1. Các địa điểm nổi tiếng nên đến
2. Thời điểm thích hợp để đi
3. Phương tiện di chuyển
4. Ước tính chi phí
5. Lời khuyên và lưu ý đặc biệt"""

FOOD_PROMPT = """Bạn là chuyên gia ẩm thực địa phương tại Việt Nam. Với thông tin:
- Địa điểm: {location}
- Sở thích: {preferences}
- Ngân sách: {budget}/người
- Số người: {number_member}
- Dị ứng: {allergy}

Hãy tư vấn về:
1. Các món đặc sản nổi tiếng
2. Địa chỉ các quán ăn ngon
3. Giá cả tham khảo
4. Thời điểm nên đến
5. Lời khuyên về vệ sinh an toàn thực phẩm"""

# Khởi tạo Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    context_window=4096,
    max_new_tokens=4096
)

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

# Define Primary Agent tools
Primary_Agent_tools = [ToAccommodation_Agent, ToDestination_Agent, ToFood_Agent, ToTransaction_Agent]

def route_primary_agent(state: State):
    """Route messages from Primary Agent to appropriate specialized agents."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToAccommodation_Agent.__name__:
            return "enter_Accommodation_Agent"
        elif tool_calls[0]["name"] == ToDestination_Agent.__name__:
            return "enter_Destination_Agent"
        elif tool_calls[0]["name"] == ToFood_Agent.__name__:
            return "enter_Food_Agent"
        elif tool_calls[0]["name"] == ToTransaction_Agent.__name__:
            return "enter_Transaction_Agent"
        return "Primary_Agent_tools"
    
    return "Primary_Agent"

def Primary_Agent(state: State):
    """Primary agent that handles initial user interactions."""
    # Initialize state if not present
    if "preferences" not in state:
        state["preferences"] = Preferences()
    if "Recommended_Tour" not in state:
        state["Recommended_Tour"] = {}
    if "dialog_state" not in state:
        state["dialog_state"] = ["Primary_Agent"]
        
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", PRIMARY_PROMPT.format(
            name=state["preferences"].name,
            number_member=state["preferences"].number_member,
            total_expense=state["preferences"].total_expense
        )),
        ("human", "{input}")
    ])
    
    # Get the last message from state
    last_message = state["messages"][-1]
    if isinstance(last_message, tuple):
        user_input = last_message[1]
    else:
        user_input = last_message.content
        
    # Format the prompt with the user's input
    formatted_prompt = prompt.format_messages(input=user_input)
    
    # Create runnable with tools
    runnable = llm.bind_tools(Primary_Agent_tools)
    
    # Invoke the LLM with the formatted messages
    response = runnable.invoke(formatted_prompt)
    return {"messages": response}

# Công cụ tìm kiếm online
def search_tool(request: str) -> list:
    """Công cụ tìm kiếm online sử dụng Tavily API."""
    search_results = TavilySearchResults(max_results=2).invoke(request)
    return search_results

# Helper functions để trích xuất thông tin từ câu hỏi
def extract_location(text: str) -> str:
    """Trích xuất địa điểm từ câu hỏi."""
    text = text.lower()
    locations = ["đà lạt", "hội an", "sapa", "phú quốc", "nha trang", "hà nội", 
                "sài gòn", "hồ chí minh", "huế", "đà nẵng", "hạ long", "quy nhơn"]
    
    for loc in locations:
        if loc in text:
            return loc.title()
    return "chưa xác định"

def extract_duration(text: str) -> str:
    """Trích xuất thời gian từ câu hỏi."""
    text = text.lower()
    if "1 ngày" in text or "một ngày" in text:
        return "1 ngày"
    elif "2 ngày" in text or "hai ngày" in text:
        return "2 ngày"
    elif "3 ngày" in text or "ba ngày" in text:
        return "3 ngày"
    elif "4 ngày" in text or "bốn ngày" in text:
        return "4 ngày"
    elif "5 ngày" in text or "năm ngày" in text:
        return "5 ngày"
    elif "1 tuần" in text or "một tuần" in text:
        return "7 ngày"
    return "3 ngày"

def extract_interests(text: str) -> str:
    """Trích xuất sở thích từ câu hỏi."""
    text = text.lower()
    interests = []
    
    interest_keywords = {
        "thiên nhiên": ["thiên nhiên", "núi", "biển", "rừng", "thác"],
        "chụp ảnh": ["chụp ảnh", "chụp hình", "photography", "check in"],
        "ẩm thực": ["ăn uống", "ẩm thực", "món ăn", "đặc sản"],
        "văn hóa": ["văn hóa", "lịch sử", "di tích", "bảo tàng"],
        "mua sắm": ["mua sắm", "shopping", "chợ"],
        "giải trí": ["giải trí", "vui chơi", "công viên", "bar", "café"]
    }
    
    for category, keywords in interest_keywords.items():
        if any(keyword in text for keyword in keywords):
            interests.append(category)
    
    return ", ".join(interests) if interests else "chưa xác định"

def extract_requirements(text: str) -> str:
    """Trích xuất yêu cầu từ câu hỏi."""
    text = text.lower()
    requirements = []
    
    req_keywords = {
        "gần trung tâm": ["trung tâm", "gần phố"],
        "gần biển": ["gần biển", "view biển"],
        "yên tĩnh": ["yên tĩnh", "không ồn ào"],
        "có hồ bơi": ["hồ bơi", "bể bơi", "swimming"],
        "có bãi đỗ xe": ["bãi đỗ xe", "parking"],
        "phù hợp gia đình": ["gia đình", "trẻ em", "family"]
    }
    
    for req, keywords in req_keywords.items():
        if any(keyword in text for keyword in keywords):
            requirements.append(req)
    
    return ", ".join(requirements) if requirements else "không có yêu cầu đặc biệt"

def extract_food_preferences(text: str) -> str:
    """Trích xuất sở thích ẩm thực từ câu hỏi."""
    text = text.lower()
    preferences = []
    
    food_keywords = {
        "hải sản": ["hải sản", "cá", "tôm", "cua", "ghẹ"],
        "đồ nướng": ["nướng", "bbq", "barbecue"],
        "món truyền thống": ["truyền thống", "đặc sản", "địa phương"],
        "chay": ["chay", "thuần chay", "vegetarian"],
        "ăn vặt": ["ăn vặt", "street food", "đồ ăn đường phố"]
    }
    
    for pref, keywords in food_keywords.items():
        if any(keyword in text for keyword in keywords):
            preferences.append(pref)
    
    return ", ".join(preferences) if preferences else "không có yêu cầu đặc biệt"

def calculate_food_budget(total_budget: str) -> str:
    """Tính toán ngân sách cho ăn uống (30% tổng ngân sách)."""
    try:
        # Lọc ra các số từ chuỗi ngân sách
        budget = float(''.join(filter(str.isdigit, total_budget)))
        
        # Nếu số có 4-9 chữ số, giả định là VNĐ
        if 1000 <= budget <= 999999999:
            food_budget = budget * 0.3
            return f"{int(food_budget):,} VNĐ"
        # Nếu số nhỏ hơn 4 chữ số, giả định là triệu VNĐ
        else:
            food_budget = budget * 1000000 * 0.3
            return f"{int(food_budget):,} VNĐ"
    except:
        return "200,000 VNĐ"

# Function để xác định agent phù hợp và tạo prompt
def determine_agent_and_prompt(user_input: str, preferences: Preferences) -> tuple[str, str]:
    """Xác định agent phù hợp và tạo prompt tương ứng."""
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ["khách sạn", "homestay", "resort", "ở đâu", "nghỉ", "phòng", "ngủ", "lưu trú"]):
        prompt = ACCOMMODATION_PROMPT.format(
            location=extract_location(user_input),
            budget=preferences.total_expense,
            number_member=preferences.number_member,
            requirements=extract_requirements(user_input)
        )
        return "accommodation", prompt
    
    elif any(word in input_lower for word in ["địa điểm", "đi đâu", "tham quan", "du lịch", "thăm quan", "điểm đến", "thắng cảnh"]):
        prompt = DESTINATION_PROMPT.format(
            location=extract_location(user_input),
            duration=extract_duration(user_input),
            number_member=preferences.number_member,
            budget=preferences.total_expense,
            interests=extract_interests(user_input)
        )
        return "destination", prompt
    
    elif any(word in input_lower for word in ["ăn", "món", "nhà hàng", "quán", "đặc sản", "ẩm thực", "đồ ăn"]):
        prompt = FOOD_PROMPT.format(
            location=extract_location(user_input),
            preferences=extract_food_preferences(user_input),
            budget=calculate_food_budget(preferences.total_expense),
            number_member=preferences.number_member,
            allergy="không có thông tin"
        )
        return "food", prompt
    
    else:
        prompt = PRIMARY_PROMPT.format(
            name=preferences.name,
            number_member=preferences.number_member,
            total_expense=preferences.total_expense
        )
        return "general", prompt

# Tools for specialized agents
class CompleteOrEscalate(BaseModel):
    """
    Một công cụ để đánh dấu nhiệm vụ hiện tại đã hoàn thành và/hoặc chuyển giao quyền kiểm soát cuộc đối thoại
    cho Primary Agent, người có thể điều chỉnh lại hướng cuộc đối thoại dựa trên nhu cầu của người dùng.
    """
    complete: bool = Field(
        ...,
        description="Vấn đề của người dùng đã được giải quyết xong chưa? Rồi thì True, Chưa thì False",
        example="False"
    )
    reason: str = Field(
        ...,
        description="Nguyên nhân tại sao đưa cuộc đối thoại về lại Primary Agent",
        example="Người dùng hỏi về chủ đề khác ngoài chuyên môn"
    )

def route_specific_agent(state: State):
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)

    if did_cancel:
        return "leave_agent"

    return route

def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant."""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the Primary Agent. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    else:
        messages.append(
            SystemMessage(
                content="Resuming dialog with the Primary Agent. Please reflect on the past conversation and assist the user as needed."
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }

def create_entry_node(agent_name: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=(
                        f"Trợ lý hiện tại là {agent_name}. Hãy xem xét lại cuộc trò chuyện giữa trợ lý chính và người dùng. "
                        "Ý định của người dùng chưa được đáp ứng. Hãy sử dụng các công cụ được cung cấp để hỗ trợ người dùng. "
                        f"Nhớ rằng, bạn là {agent_name}, và việc đặt chỗ, cập nhật hoặc bất kỳ hành động nào khác sẽ không hoàn tất "
                        f"cho đến khi bạn đã gọi thành công công cụ phù hợp. "
                        "Nếu người dùng thay đổi ý định hoặc cần trợ giúp cho các tác vụ khác, hãy dừng cuộc trò chuyện "
                        "để trợ lý chính tiếp quản cuộc trò chuyện. "
                        "Không được đề cập đến việc bạn là ai – chỉ hành động như một trợ lý thay mặt cho hệ thống."
                    ),
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": agent_name,
        }
    return entry_node

def Accommodation_Agent(state: State):
    """Accommodation agent that handles accommodation-related queries."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", ACCOMMODATION_PROMPT.format(
            location=extract_location(state["messages"][-1][1]),
            budget=state["preferences"].total_expense,
            number_member=state["preferences"].number_member,
            requirements=extract_requirements(state["messages"][-1][1])
        )),
        ("human", "{input}")
    ])
    
    formatted_prompt = prompt.format_messages(input=state["messages"][-1][1])
    runnable = llm.bind_tools([search_tool, CompleteOrEscalate])
    response = runnable.invoke(formatted_prompt)
    return {"messages": response}

def Destination_Agent(state: State):
    """Destination agent that handles destination-related queries."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", DESTINATION_PROMPT.format(
            location=extract_location(state["messages"][-1][1]),
            duration=extract_duration(state["messages"][-1][1]),
            number_member=state["preferences"].number_member,
            budget=state["preferences"].total_expense,
            interests=extract_interests(state["messages"][-1][1])
        )),
        ("human", "{input}")
    ])
    
    formatted_prompt = prompt.format_messages(input=state["messages"][-1][1])
    runnable = llm.bind_tools([search_tool, CompleteOrEscalate])
    response = runnable.invoke(formatted_prompt)
    return {"messages": response}

def Food_Agent(state: State):
    """Food agent that handles food-related queries."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", FOOD_PROMPT.format(
            location=extract_location(state["messages"][-1][1]),
            preferences=extract_food_preferences(state["messages"][-1][1]),
            budget=calculate_food_budget(state["preferences"].total_expense),
            number_member=state["preferences"].number_member,
            allergy="không có thông tin"
        )),
        ("human", "{input}")
    ])
    
    formatted_prompt = prompt.format_messages(input=state["messages"][-1][1])
    runnable = llm.bind_tools([search_tool, CompleteOrEscalate])
    response = runnable.invoke(formatted_prompt)
    return {"messages": response}

def Transaction_Agent(state: State):
    """Transaction agent that handles transaction-related queries."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia về giao dịch và thanh toán. Hãy giúp người dùng thực hiện các giao dịch an toàn và thuận tiện."),
        ("human", "{input}")
    ])
    
    formatted_prompt = prompt.format_messages(input=state["messages"][-1][1])
    runnable = llm.bind_tools([CompleteOrEscalate])
    response = runnable.invoke(formatted_prompt)
    return {"messages": response}

def initialize_graph():
    """Initialize and return the graph."""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("Primary_Agent", Primary_Agent)
    builder.add_node("Primary_Agent_tools", create_tool_node_with_fallback(Primary_Agent_tools))

    # Add specialized agent nodes
    builder.add_node("Accommodation_Agent", Accommodation_Agent)
    builder.add_node("Destination_Agent", Destination_Agent)
    builder.add_node("Food_Agent", Food_Agent)
    builder.add_node("Transaction_Agent", Transaction_Agent)

    # Add specialized agent tools nodes
    builder.add_node("Accommodation_Agent_tools", create_tool_node_with_fallback([search_tool, CompleteOrEscalate]))
    builder.add_node("Destination_Agent_tools", create_tool_node_with_fallback([search_tool, CompleteOrEscalate]))
    builder.add_node("Food_Agent_tools", create_tool_node_with_fallback([search_tool, CompleteOrEscalate]))
    builder.add_node("Transaction_Agent_tools", create_tool_node_with_fallback([CompleteOrEscalate]))

    # Add entry nodes for specialized agents
    builder.add_node("enter_Accommodation_Agent", create_entry_node("Accommodation_Agent"))
    builder.add_node("enter_Destination_Agent", create_entry_node("Destination_Agent"))
    builder.add_node("enter_Food_Agent", create_entry_node("Food_Agent"))
    builder.add_node("enter_Transaction_Agent", create_entry_node("Transaction_Agent"))

    # Add leave agent node
    builder.add_node("leave_agent", pop_dialog_state)

    # Add edges with routing
    builder.add_edge(START, "Primary_Agent")
    
    # Primary Agent routing
    builder.add_conditional_edges(
        "Primary_Agent",
        route_primary_agent,
        {
            "enter_Accommodation_Agent": "Accommodation_Agent",
            "enter_Destination_Agent": "Destination_Agent",
            "enter_Food_Agent": "Food_Agent",
            "enter_Transaction_Agent": "Transaction_Agent",
            "Primary_Agent_tools": "Primary_Agent_tools",
            END: END
        }
    )
    builder.add_edge("Primary_Agent_tools", "Primary_Agent")

    # Specialized agents routing
    for agent in ["Accommodation", "Destination", "Food", "Transaction"]:
        # Add edges from agent to tools
        builder.add_conditional_edges(
            f"{agent}_Agent",
            route_specific_agent,
            {
                "tools": f"{agent}_Agent_tools",
                "leave_agent": "leave_agent",
                END: END
            }
        )
        
        # Add edge from tools back to agent
        builder.add_edge(f"{agent}_Agent_tools", f"{agent}_Agent")
        
        # Add edge from entry node to agent
        builder.add_edge(f"enter_{agent}_Agent", f"{agent}_Agent")

    # Add edge from leave_agent back to Primary_Agent
    builder.add_edge("leave_agent", "Primary_Agent")

    # Compile graph
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)

# Thiết lập trang
st.set_page_config(
    page_title="Tour Guide Assistant",
    page_icon="🏖️",
    layout="wide"
)

# Custom CSS để tạo giao diện đẹp hơn
st.markdown("""
<style>
.stApp {
    background-color: #f0f2f6;
}

.main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.stTitle {
    color: #1e3a8a;
    font-size: 2.5rem !important;
    text-align: center;
    margin-bottom: 2rem !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.chat-container {
    background-color: white;
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.chat-message {
    padding: 1rem;
    border-radius: 1rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    max-width: 80%;
}

.user-message {
    background-color: #2196f3;
    color: #ffffff;
    margin-left: auto;
    margin-right: 1rem;
    border: 1px solid #1976d2;
}

.bot-message {
    background-color: #ffffff;
    color: #2c3e50;
    margin-right: auto;
    margin-left: 1rem;
    border: 1px solid #e0e0e0;
}

.message-content {
    display: flex;
    align-items: flex-start;
}

.message-text {
    margin-left: 1rem;
    line-height: 1.6;
    font-size: 1.05rem;
}

.user-message b {
    color: #e3f2fd;
    font-size: 0.9rem;
    text-transform: uppercase;
}

.bot-message b {
    color: #1565c0;
    font-size: 0.9rem;
    text-transform: uppercase;
}

/* Style cho input và button */
.stTextInput input {
    border: 2px solid #e0e0e0;
    border-radius: 0.5rem;
    padding: 0.75rem;
    font-size: 1rem;
    color: #2c3e50;
    background-color: #ffffff;
}

.stTextInput input:focus {
    border-color: #1e88e5;
    box-shadow: 0 0 0 2px rgba(30,136,229,0.2);
}

.stButton button {
    background-color: #1976d2 !important;
    color: #ffffff !important;
    border-radius: 0.5rem !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    border: none !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.stButton button:hover {
    background-color: #1565c0 !important;
    transform: translateY(-2px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Style cho footer */
.footer {
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-top: 2rem;
    border: 1px solid #e0e0e0;
}

.footer h3 {
    color: #1565c0;
    margin-bottom: 1.5rem;
    font-size: 1.3rem;
    font-weight: 600;
}

.footer ul {
    list-style-type: none;
    padding: 0;
}

.footer li {
    color: #1a237e;  /* Màu xanh đậm cho text */
    margin-bottom: 1rem;
    padding: 0.8rem 1rem;
    position: relative;
    font-size: 1rem;
    background-color: #e3f2fd;  /* Nền xanh nhạt */
    border-radius: 0.5rem;
    border-left: 4px solid #1565c0;  /* Viền trái đậm */
    transition: all 0.3s ease;
    cursor: pointer;
}

.footer li:hover {
    background-color: #bbdefb;
    transform: translateX(5px);
}

.footer li:before {
    content: "💡";  /* Thay bullet point bằng emoji */
    margin-right: 0.5rem;
}

/* Style cho sidebar */
.sidebar .stMarkdown {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

.sidebar h3 {
    color: #1565c0;
    margin-bottom: 1rem;
}

.sidebar p {
    color: #2c3e50;
    margin-bottom: 0.5rem;
}

/* Style cho form */
.stForm {
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.stForm .stMarkdown h3 {
    color: #1565c0;
    margin-bottom: 2rem;
}

.stTextInput > label {
    color: #2c3e50;
    font-weight: 500;
}

.stFormSubmitButton > button {
    background-color: #1565c0 !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: 0.5rem !important;
    border: none !important;
    transition: all 0.3s ease !important;
}

.stFormSubmitButton > button:hover {
    background-color: #0d47a1 !important;
    transform: translateY(-2px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Responsive design */
@media (max-width: 768px) {
    .chat-message {
        max-width: 90%;
    }
}

/* Style cho welcome message */
.welcome-header {
    background: linear-gradient(135deg, #1976d2, #1565c0);
    color: white;
    padding: 1.5rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.welcome-header h3 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.welcome-emoji {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    display: block;
}

/* Style cho form container */
.form-container {
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border: 1px solid #e0e0e0;
}
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'preferences' not in st.session_state:
    st.session_state.preferences = Preferences()
if 'preferences_set' not in st.session_state:
    st.session_state.preferences_set = False

# Hiển thị form preferences nếu chưa được thiết lập
if not st.session_state.preferences_set:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="welcome-header">
            <span class="welcome-emoji">👋</span>
            <h3>Chào mừng bạn!</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Hãy cho tôi biết một chút về bạn</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("preferences_form"):
        name = st.text_input("Bạn tên gì?", value=st.session_state.preferences.name)
        number_member = st.text_input("Số thành viên trong nhóm?", value=st.session_state.preferences.number_member)
        total_expense = st.text_input("Tổng chi phí cho chuyến đi?", value=st.session_state.preferences.total_expense)
        
        if st.form_submit_button("Bắt đầu trò chuyện"):
            st.session_state.preferences = Preferences(
                name=name,
                number_member=number_member,
                total_expense=total_expense
            )
            st.session_state.preferences_set = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Hiển thị chat interface nếu đã có preferences
else:
    st.markdown('<h1 class="stTitle">🏖️ Tour Guide Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="message-content">
                        <div class="message-text">
                            <b>Bạn:</b><br>{message["content"]}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <div class="message-content">
                        <div class="message-text">
                            <b>Assistant:</b><br>{message["content"]}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Input cho người dùng
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                label="Câu hỏi của bạn",
                key="user_input", 
                placeholder="Nhập câu hỏi của bạn về du lịch...",
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Gửi", help="Nhấn để gửi câu hỏi của bạn")

    # Streamlit interface
    if 'graph' not in st.session_state:
        st.session_state.graph = initialize_graph()

    if 'config' not in st.session_state:
        st.session_state.config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
            }
        }

    if 'printed' not in st.session_state:
        st.session_state.printed = set()

    def process_message(message, printed_set):
        """Process and format agent messages."""
        if not isinstance(message, HumanMessage):
            if message.id not in printed_set:
                msg_repr = message.content
                if len(msg_repr) > 1500:  # Truncate long messages
                    msg_repr = msg_repr[:1500] + " ... (truncated)"
                printed_set.add(message.id)
                return msg_repr
        return None

    # Xử lý khi người dùng gửi tin nhắn
    if send_button and user_input:
        # Thêm tin nhắn của người dùng vào lịch sử
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Debug log
        st.write("Processing message:", user_input)
        
        # Process through the agent graph
        events = st.session_state.graph.stream(
            {"messages": ("user", user_input)},
            st.session_state.config,
            stream_mode="values"
        )
        
        # Process each event
        for event in events:
            # Debug log
            st.write("Event received:", event)
            
            message = event.get("messages")
            if message:
                if isinstance(message, list):
                    message = message[-1]
                
                # Debug log
                st.write("Processing bot response:", message)
                
                bot_response = process_message(message, st.session_state.printed)
                if bot_response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_response
                    })
            
            # Update current state if needed
            current_state = event.get("dialog_state")
            if current_state:
                st.session_state.current_agent = current_state[-1]
        
        st.rerun()

    # Hiển thị agent hiện tại trong sidebar nếu có
    if hasattr(st.session_state, 'current_agent'):
        with st.sidebar:
            st.markdown(f"**Current Agent:** {st.session_state.current_agent}")

    # Footer với gợi ý
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown('<h3>💡 Gợi ý câu hỏi:</h3>', unsafe_allow_html=True)

    # Tạo danh sách gợi ý có thể click
    suggestions = [
        "Gợi ý cho tôi một số địa điểm du lịch nổi tiếng ở Đà Lạt",
        "Có những nhà hàng nào ngon ở Hội An?",
        "Thời điểm nào thích hợp để du lịch Sapa?",
        "Gợi ý lịch trình 3 ngày ở Phú Quốc"
    ]

    # Hiển thị gợi ý dưới dạng các nút có thể click
    for suggestion in suggestions:
        if st.button(suggestion, key=f"suggestion_{suggestion}"):
            # Thêm tin nhắn của người dùng vào lịch sử
            st.session_state.messages.append({"role": "user", "content": suggestion})
            
            # Process through the agent graph
            events = st.session_state.graph.stream(
                {"messages": ("user", suggestion)},
                st.session_state.config,
                stream_mode="values"
            )
            
            # Process each event
            for event in events:
                message = event.get("messages")
                if message:
                    if isinstance(message, list):
                        message = message[-1]
                    
                    bot_response = process_message(message, st.session_state.printed)
                    if bot_response:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": bot_response
                        })
                
                # Update current state if needed
                current_state = event.get("dialog_state")
                if current_state:
                    st.session_state.current_agent = current_state[-1]
            
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Hiển thị preferences và nút reset
    with st.sidebar:
        st.markdown("### 👤 Thông tin của bạn")
        st.write(f"**Tên:** {st.session_state.preferences.name}")
        st.write(f"**Số thành viên:** {st.session_state.preferences.number_member}")
        st.write(f"**Ngân sách:** {st.session_state.preferences.total_expense}")
        
        if st.button("🔄 Thay đổi thông tin"):
            st.session_state.preferences_set = False
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🗑️ Xóa lịch sử"):
            st.session_state.messages = []
            st.rerun() 