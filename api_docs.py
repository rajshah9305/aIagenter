from flask import Blueprint, jsonify, render_template_string
from typing import Dict, Any, List
import json

api_docs_bp = Blueprint('api_docs', __name__)

# OpenAPI 3.0 specification for AgentOrchestra
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "AgentOrchestra API",
        "description": "Comprehensive multi-agent system for managing and orchestrating AI agents",
        "version": "1.0.0",
        "contact": {
            "name": "AgentOrchestra Team",
            "email": "support@agentorchestra.ai"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000/api",
            "description": "Development server"
        }
    ],
    "tags": [
        {
            "name": "agents",
            "description": "Agent management operations"
        },
        {
            "name": "workflows",
            "description": "Workflow management operations"
        },
        {
            "name": "tasks",
            "description": "Task distribution and management"
        },
        {
            "name": "monitoring",
            "description": "Real-time monitoring and metrics"
        },
        {
            "name": "communication",
            "description": "Inter-agent communication"
        },
        {
            "name": "orchestration",
            "description": "Agent orchestration operations"
        }
    ],
    "paths": {
        "/agents": {
            "get": {
                "tags": ["agents"],
                "summary": "List all agents",
                "description": "Retrieve a list of all registered agents",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "agents": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Agent"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["agents"],
                "summary": "Create a new agent",
                "description": "Register a new agent in the system",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AgentCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Agent created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "agent_id": {"type": "string"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid input",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/agents/{agent_id}": {
            "get": {
                "tags": ["agents"],
                "summary": "Get agent details",
                "description": "Retrieve details of a specific agent",
                "parameters": [
                    {
                        "name": "agent_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Unique identifier of the agent"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "agent": {"$ref": "#/components/schemas/Agent"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Agent not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            },
            "put": {
                "tags": ["agents"],
                "summary": "Update agent",
                "description": "Update an existing agent's configuration",
                "parameters": [
                    {
                        "name": "agent_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AgentUpdate"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Agent updated successfully"
                    },
                    "404": {
                        "description": "Agent not found"
                    }
                }
            },
            "delete": {
                "tags": ["agents"],
                "summary": "Delete agent",
                "description": "Remove an agent from the system",
                "parameters": [
                    {
                        "name": "agent_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Agent deleted successfully"
                    },
                    "404": {
                        "description": "Agent not found"
                    }
                }
            }
        },
        "/tasks": {
            "post": {
                "tags": ["tasks"],
                "summary": "Submit a new task",
                "description": "Submit a task for execution by an agent",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TaskCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Task submitted successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "task_id": {"type": "string"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/tasks/{task_id}": {
            "get": {
                "tags": ["tasks"],
                "summary": "Get task status",
                "description": "Retrieve the status and details of a specific task",
                "parameters": [
                    {
                        "name": "task_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "task": {"$ref": "#/components/schemas/Task"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/workflows": {
            "get": {
                "tags": ["workflows"],
                "summary": "List workflows",
                "description": "Retrieve a list of all workflow definitions",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "workflows": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Workflow"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["workflows"],
                "summary": "Create workflow",
                "description": "Create a new workflow definition",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WorkflowCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Workflow created successfully"
                    }
                }
            }
        },
        "/workflows/{workflow_id}/execute": {
            "post": {
                "tags": ["workflows"],
                "summary": "Execute workflow",
                "description": "Start execution of a workflow",
                "parameters": [
                    {
                        "name": "workflow_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "input_data": {
                                        "type": "object",
                                        "description": "Input data for workflow execution"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Workflow execution started"
                    }
                }
            }
        },
        "/monitoring/metrics": {
            "get": {
                "tags": ["monitoring"],
                "summary": "Get system metrics",
                "description": "Retrieve real-time system metrics",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Metrics"}
                            }
                        }
                    }
                }
            }
        },
        "/monitoring/alerts": {
            "get": {
                "tags": ["monitoring"],
                "summary": "Get alerts",
                "description": "Retrieve system alerts",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "alerts": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Alert"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Agent": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique identifier"},
                    "name": {"type": "string", "description": "Agent name"},
                    "framework": {"type": "string", "enum": ["AutoGen", "CrewAI", "LangGraph", "MetaGPT", "BabyAGI"]},
                    "status": {"type": "string", "enum": ["active", "paused", "error", "offline"]},
                    "version": {"type": "string", "description": "Agent version"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of agent capabilities"
                    },
                    "configuration": {
                        "type": "object",
                        "description": "Agent configuration parameters"
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "last_seen": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "framework", "status"]
            },
            "AgentCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "framework": {"type": "string", "enum": ["AutoGen", "CrewAI", "LangGraph", "MetaGPT", "BabyAGI"]},
                    "version": {"type": "string"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "configuration": {"type": "object"}
                },
                "required": ["name", "framework"]
            },
            "AgentUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "paused", "error", "offline"]},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "configuration": {"type": "object"}
                }
            },
            "Task": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "task_data": {"type": "object"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
                    "status": {"type": "string", "enum": ["pending", "queued", "running", "completed", "failed", "cancelled"]},
                    "created_at": {"type": "string", "format": "date-time"},
                    "started_at": {"type": "string", "format": "date-time"},
                    "completed_at": {"type": "string", "format": "date-time"},
                    "result": {"type": "object"},
                    "error": {"type": "string"}
                }
            },
            "TaskCreate": {
                "type": "object",
                "properties": {
                    "task_data": {"type": "object"},
                    "agent_id": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "default": "normal"},
                    "timeout_seconds": {"type": "integer", "default": 300},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["task_data"]
            },
            "Workflow": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "version": {"type": "string"},
                    "nodes": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/components/schemas/WorkflowNode"}
                    },
                    "connections": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/WorkflowConnection"}
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                }
            },
            "WorkflowNode": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["agent", "condition", "action", "parallel", "sequential"]},
                    "name": {"type": "string"},
                    "config": {"type": "object"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    }
                }
            },
            "WorkflowConnection": {
                "type": "object",
                "properties": {
                    "from_node_id": {"type": "string"},
                    "to_node_id": {"type": "string"},
                    "condition": {"type": "string"},
                    "label": {"type": "string"}
                }
            },
            "WorkflowCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "version": {"type": "string", "default": "1.0"},
                    "nodes": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/WorkflowNode"}
                    },
                    "connections": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/WorkflowConnection"}
                    }
                },
                "required": ["name", "nodes"]
            },
            "Metrics": {
                "type": "object",
                "properties": {
                    "system": {
                        "type": "object",
                        "properties": {
                            "cpu_usage": {"type": "number"},
                            "memory_usage": {"type": "number"},
                            "disk_usage": {"type": "number"}
                        }
                    },
                    "agents": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "active": {"type": "integer"},
                            "paused": {"type": "integer"},
                            "error": {"type": "integer"}
                        }
                    },
                    "tasks": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "queued": {"type": "integer"},
                            "running": {"type": "integer"},
                            "completed": {"type": "integer"},
                            "failed": {"type": "integer"}
                        }
                    },
                    "workflows": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "running": {"type": "integer"},
                            "completed": {"type": "integer"}
                        }
                    }
                }
            },
            "Alert": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["info", "warning", "error", "critical"]},
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "status": {"type": "string", "enum": ["active", "acknowledged", "resolved"]},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error": {"type": "string", "description": "Error message"},
                    "code": {"type": "string", "description": "Error code"}
                },
                "required": ["success", "error"]
            }
        },
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    },
    "security": [
        {"bearerAuth": []},
        {"apiKey": []}
    ]
}

# Swagger UI HTML template
SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AgentOrchestra API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/docs/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>
"""

@api_docs_bp.route('/docs')
def swagger_ui():
    """Serve Swagger UI for API documentation."""
    return render_template_string(SWAGGER_UI_HTML)

@api_docs_bp.route('/docs/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification as JSON."""
    return jsonify(OPENAPI_SPEC)

@api_docs_bp.route('/docs/redoc')
def redoc_ui():
    """Serve ReDoc UI for API documentation."""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgentOrchestra API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/docs/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return render_template_string(redoc_html)

@api_docs_bp.route('/docs/postman')
def postman_collection():
    """Generate Postman collection from OpenAPI spec."""
    # Convert OpenAPI to Postman collection format
    collection = {
        "info": {
            "name": "AgentOrchestra API",
            "description": "Comprehensive multi-agent system API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:5000/api",
                "type": "string"
            }
        ]
    }
    
    # Convert paths to Postman requests
    for path, methods in OPENAPI_SPEC["paths"].items():
        folder = {
            "name": path,
            "item": []
        }
        
        for method, spec in methods.items():
            request_item = {
                "name": spec.get("summary", f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "url": {
                        "raw": "{{baseUrl}}" + path,
                        "host": ["{{baseUrl}}"],
                        "path": path.strip("/").split("/")
                    }
                }
            }
            
            # Add request body if present
            if "requestBody" in spec:
                request_item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps({}, indent=2)
                }
            
            folder["item"].append(request_item)
        
        collection["item"].append(folder)
    
    return jsonify(collection)

def generate_api_documentation() -> Dict[str, Any]:
    """Generate comprehensive API documentation."""
    return {
        "title": "AgentOrchestra API Documentation",
        "version": "1.0.0",
        "description": "Complete API reference for the AgentOrchestra platform",
        "base_url": "http://localhost:5000/api",
        "authentication": {
            "types": ["Bearer Token", "API Key"],
            "description": "Most endpoints require authentication using either a JWT bearer token or API key"
        },
        "rate_limiting": {
            "default": "100 requests per hour",
            "authenticated": "1000 requests per hour"
        },
        "endpoints": {
            "agents": {
                "description": "Manage AI agents in the system",
                "operations": ["GET", "POST", "PUT", "DELETE"],
                "examples": {
                    "create_agent": {
                        "method": "POST",
                        "url": "/agents",
                        "body": {
                            "name": "Research Assistant",
                            "framework": "AutoGen",
                            "capabilities": ["research", "analysis", "reporting"],
                            "configuration": {
                                "model": "gpt-4",
                                "temperature": 0.7
                            }
                        }
                    }
                }
            },
            "tasks": {
                "description": "Submit and manage tasks for agent execution",
                "operations": ["GET", "POST", "DELETE"],
                "examples": {
                    "submit_task": {
                        "method": "POST",
                        "url": "/tasks",
                        "body": {
                            "task_data": {
                                "instruction": "Analyze the quarterly sales data",
                                "data_source": "sales_q4_2023.csv"
                            },
                            "agent_id": "agent-123",
                            "priority": "high",
                            "timeout_seconds": 600
                        }
                    }
                }
            },
            "workflows": {
                "description": "Create and execute multi-agent workflows",
                "operations": ["GET", "POST", "PUT", "DELETE"],
                "examples": {
                    "create_workflow": {
                        "method": "POST",
                        "url": "/workflows",
                        "body": {
                            "name": "Data Analysis Pipeline",
                            "description": "Automated data analysis workflow",
                            "nodes": [
                                {
                                    "id": "node-1",
                                    "type": "agent",
                                    "name": "Data Collector",
                                    "config": {"agent_id": "collector-agent"}
                                },
                                {
                                    "id": "node-2",
                                    "type": "agent",
                                    "name": "Data Analyzer",
                                    "config": {"agent_id": "analyzer-agent"}
                                }
                            ],
                            "connections": [
                                {
                                    "from_node_id": "node-1",
                                    "to_node_id": "node-2"
                                }
                            ]
                        }
                    }
                }
            }
        },
        "error_codes": {
            "400": "Bad Request - Invalid input parameters",
            "401": "Unauthorized - Authentication required",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource does not exist",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error - Server error occurred"
        },
        "webhooks": {
            "description": "Configure webhooks for real-time notifications",
            "events": [
                "agent.created",
                "agent.status_changed",
                "task.completed",
                "task.failed",
                "workflow.started",
                "workflow.completed",
                "alert.triggered"
            ]
        }
    }

@api_docs_bp.route('/docs/reference')
def api_reference():
    """Serve comprehensive API reference documentation."""
    docs = generate_api_documentation()
    return jsonify(docs)

