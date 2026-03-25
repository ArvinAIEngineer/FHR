from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the message")


class ChatResponseChunk(BaseModel):
    type: str = Field(..., description="Type of response chunk")
    data: Any = Field(..., description="The data payload")


class Attachment(BaseModel):
    fileName: str = Field(..., description="Name of the file")
    filePath: str = Field(..., description="Path to the file")
    contentType: str = Field(..., description="MIME type of the file")
    fileContent: str = Field(..., description="Base64 encoded content of the file")
    fileSize: int = Field(..., description="Size of the file in bytes")
    

class ChatRequest(BaseModel):
    conversationId: int = Field(..., description="Unique identifier for the conversation")
    personId: int = Field(..., description="Unique identifier for the person")
    avatarId: int = Field(..., description="Unique identifier for the avatar")
    sessionStart: bool = Field(..., description="Indicates if this is the start of a session")
    language: str = Field(..., description="Language of the conversation")
    conversationTitle: Optional[str] = Field(..., description="Title of the conversation")
    conversationMessage: str = Field(..., description="Message content of the conversation")
    channel: str = Field(..., description="Channel through which the conversation is happening")
    inputType: str = Field(..., description="Type of input (e.g., text, voice)")
    outputType: str = Field(..., description="Type of output (e.g., text, voice)")
    personalInfo: dict = Field(..., description="Dict of personal information items")
    attachments: Optional[List[Attachment]] = Field(default_factory=list, description="List of attachments associated with the message")

class ImageData(BaseModel):
    fileName: str = Field(..., description="Name of the image file")
    fileSize: str = Field(..., description="Size of the image file")
    fileData: str = Field(..., description="Base64 encoded image data")
    url: str = Field(..., description="URL of the image")


class VoiceData(BaseModel):
    audioBase64: str = Field(..., description="Base64 encoded audio data")
    contentType: str = Field(..., description="MIME type of the audio file")


class WidgetData(BaseModel):
    widgetType: str = Field(..., description="Type of widget")
    data: List[str] = Field(..., description="List of data strings for the widget")


class GraphIndex(BaseModel):
    name: str = Field(..., description="Name of the graph index")
    color: str = Field(..., description="Color associated with the graph index")


class GraphDatum(BaseModel):
    value: int = Field(..., description="Value of the graph datum")
    title: str = Field(..., description="Title of the graph datum")
    color: str = Field(..., description="Color associated with the graph datum")


class GraphData(BaseModel):
    graphType: str = Field(..., description="Type of the graph (e.g., bar, line)")
    indexs: List[GraphIndex] = Field(..., description="List of graph indices")
    data: List[GraphDatum] = Field(..., description="List of graph data points")


class FileData(BaseModel):
    fileName: str = Field(..., description="Name of the file")
    fileSize: str = Field(..., description="Size of the file")
    file: str = Field(..., description="Base64 encoded file data")
    url: str = Field(..., description="URL of the file")
    fileExt: str = Field(..., description="File extension of the file")


class VideoData(BaseModel):
    fileName: str = Field(..., description="Name of the video file")
    fileSize: str = Field(..., description="Size of the video file")
    fileData: str = Field(..., description="Base64 encoded video data")
    url: str = Field(..., description="URL of the video")


class TableRow(BaseModel):
    att1: str = Field(..., description="Attribute 1")
    att2: str = Field(..., description="Attribute 2")
    att3: str = Field(..., description="Attribute 3")


class NavigationParams(BaseModel):
    itemId: int = Field(..., description="ID of the navigation item")
    itemName: str = Field(..., description="Name of the navigation item")


class NavigationData(BaseModel):
    targetScreen: str = Field(..., description="Target screen for navigation")
    params: NavigationParams = Field(..., description="Parameters for navigation")


class ActionButton(BaseModel):
    title: str = Field(..., description="Title of the action button")
    action: str = Field(..., description="Action to be performed on button click")


class ReferenceData(BaseModel):
    documentId: str = Field(..., description="ID of the reference document")
    documentName: str = Field(..., description="Name of the reference document")
    pageNumber: str = Field(..., description="Page number of the reference")
    screenshotUrl: str = Field(..., description="Page image URL of the reference")


class ResponseData(BaseModel):
    conversationId: int = Field(..., description="ID of the conversation")
    messageId: int = Field(..., description="ID of the message")
    widgetType: str = Field(..., description="Type of the widget")
    switchAvatar: bool = Field(..., description="Boolean flag to switch avatar")
    avatarId: int = Field(..., description="ID of the avatar to switch to")
    textData: str = Field(..., description="Text data of the response")
    voiceData: Optional[List[VoiceData]] = Field(None, description="List of voice data objects")
    widgetData: Optional[List[WidgetData]] = Field(default_factory=list, description="List of widget data")
    faQsData: List[str] = Field(default_factory=list, description="List of FAQ strings")
    referenceData: List[ReferenceData] = Field(default_factory=list, description="List of reference data")


class ChatResponseModel(BaseModel):
    success: bool = Field(..., description="Indicates if the response was successful")
    message: str = Field(..., description="Message describing the response")
    statusCode: int = Field(..., description="HTTP status code of the response")
    data: Optional[ResponseData] = Field(None, description="Response data object")
    errors: List[str] = Field(default_factory=list, description="List of error messages")