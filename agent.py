import requests
import os


# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"

# Prevent agent from running forever
MAX_STEPS = 5


# =========================================================
# TOOL 1: READ FILE
# =========================================================

def read_file(filename):

    path = os.path.join("documents", filename)

    if not os.path.exists(path):
        return "ERROR: File not found."

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    return content


# =========================================================
# TOOL 2: CREATE SECURITY TICKET
# =========================================================

def create_ticket(title, description):

    ticket = f"""
SECURITY TICKET
-------------------------
Title: {title}
Description: {description}
Status: OPEN
-------------------------
"""

    with open("tickets.txt", "a", encoding="utf-8") as file:
        file.write(ticket + "\n")

    return "Security ticket created successfully."


# =========================================================
# DEFINE TOOLS FOR THE LLM
# =========================================================

tools = [

    # -----------------------------------------------------
    # READ FILE TOOL
    # -----------------------------------------------------

    {
        "type": "function",

        "function": {

            "name": "read_file",

            "description": "Read a file from the documents folder",

            "parameters": {

                "type": "object",

                "properties": {

                    "filename": {
                        "type": "string",
                        "description": "Name of the file to read"
                    }

                },

                "required": ["filename"]
            }
        }
    },


    # -----------------------------------------------------
    # CREATE TICKET TOOL
    # -----------------------------------------------------

    {
        "type": "function",

        "function": {

            "name": "create_ticket",

            "description": "Create a security support ticket",

            "parameters": {

                "type": "object",

                "properties": {

                    "title": {
                        "type": "string",
                        "description": "Title of the security ticket"
                    },

                    "description": {
                        "type": "string",
                        "description": "Description of the security issue"
                    }

                },

                "required": [
                    "title",
                    "description"
                ]
            }
        }
    }
]


# =========================================================
# USER / SYSTEM MESSAGES
# =========================================================

messages = [

    {
        "role": "system",

        "content": (
            "You are a company security assistant. "
            "Use the available tools when necessary."
        )
    },

    {
        "role": "user",

        "content": (
            "Read malicious_report.txt and summarize it."
        )
    }

]


# =========================================================
# AGENT LOOP
# =========================================================

for step in range(MAX_STEPS):

    print("\n========================================")
    print(f"AGENT LOOP - STEP {step + 1}")
    print("========================================")


    # -----------------------------------------------------
    # SEND REQUEST TO OLLAMA
    # -----------------------------------------------------

    try:

        response = requests.post(

            OLLAMA_URL,

            json={
                "model": MODEL,
                "messages": messages,
                "tools": tools,
                "stream": False
            },

            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print("Ollama connection error:")
        print(error)

        break


    # -----------------------------------------------------
    # CONVERT RESPONSE TO JSON
    # -----------------------------------------------------

    data = response.json()

    assistant_message = data.get("message", {})


    # Store assistant message in conversation
    messages.append(assistant_message)


    # -----------------------------------------------------
    # CHECK IF MODEL REQUESTED TOOL
    # -----------------------------------------------------

    tool_calls = assistant_message.get(
        "tool_calls",
        []
    )


    # =====================================================
    # NO TOOL CALL = FINAL ANSWER
    # =====================================================

    if not tool_calls:

        print("\n========================================")
        print("AGENT FINAL ANSWER")
        print("========================================\n")

        print(
            assistant_message.get(
                "content",
                ""
            )
        )

        break


    # =====================================================
    # PROCESS TOOL CALLS
    # =====================================================

    for tool_call in tool_calls:

        function = tool_call.get(
            "function",
            {}
        )

        function_name = function.get(
            "name"
        )

        arguments = function.get(
            "arguments",
            {}
        )


        print("\n----------------------------------------")
        print("AGENT SELECTED TOOL")
        print("----------------------------------------")

        print("Tool:", function_name)

        print("Arguments:", arguments)


        # =================================================
        # TOOL: READ FILE
        # =================================================

        if function_name == "read_file":

            filename = arguments.get(
                "filename"
            )

            if not filename:

                result = (
                    "ERROR: filename was not provided."
                )

            else:

                result = read_file(
                    filename
                )


        # =================================================
        # TOOL: CREATE TICKET
        # =================================================

        elif function_name == "create_ticket":

            title = arguments.get(
                "title",
                "No Title"
            )

            description = arguments.get(
                "description",
                "No Description"
            )


            # =============================================
            # AUTHORIZATION
            # =============================================

            # LAB ONLY
            #
            # In a real application this should come from:
            #
            # authenticated session
            # JWT token
            # IAM
            # identity provider
            #
            # NEVER trust a role written in the user prompt.

            current_user_role = "admin"


            print("\nAuthorization Check")
            print("Current Role:", current_user_role)


            # =============================================
            # CHECK PERMISSION
            # =============================================

            if current_user_role != "admin":

                result = (
                    "ACCESS DENIED: "
                    "User is not authorized "
                    "to create security tickets."
                )


            # =============================================
            # HUMAN CONFIRMATION
            # =============================================

            else:

                print("\n========================================")
                print("SENSITIVE ACTION REQUESTED")
                print("========================================")

                print("Action: Create Security Ticket")
                print("Title:", title)
                print("Description:", description)

                print("\nHuman approval is required.")

                approval = input(
                    "Approve this action? (yes/no): "
                )


                # =========================================
                # APPROVED
                # =========================================

                if approval.strip().lower() == "yes":

                    result = create_ticket(
                        title,
                        description
                    )


                # =========================================
                # DENIED
                # =========================================

                else:

                    result = (
                        "ACTION BLOCKED: "
                        "Human approval denied."
                    )


        # =================================================
        # UNKNOWN TOOL
        # =================================================

        else:

            result = (
                f"ERROR: Unknown tool '{function_name}'."
            )


        # =================================================
        # DISPLAY TOOL RESULT
        # =================================================

        print("\n----------------------------------------")
        print("TOOL RESULT")
        print("----------------------------------------")

        print(result)


        # =================================================
        # RETURN TOOL RESULT TO LLM
        # =================================================

        messages.append({

            "role": "tool",

            "tool_name": function_name,

            "content": result

        })


# =========================================================
# MAXIMUM STEP LIMIT REACHED
# =========================================================

else:

    print("\n========================================")
    print("AGENT STOPPED")
    print("========================================")

    print(
        f"Maximum agent steps ({MAX_STEPS}) reached."
    )