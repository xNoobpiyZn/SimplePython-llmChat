from openai import OpenAI
from tools import (Model_AvailableTools, Model_AvailableTools_Func)
import json

Model_API = OpenAI(base_url="http://localhost:18000/v1", api_key="Localhost")
Model_MemoryShort = [
    {"role":"system", "content":"you are helpful lazy assistant"}
]

while True:
    # get user input
    User_input = input(">> ")
    User_talkToModel = False

    # user special command ( skip talk to model )
    if User_input == "/exit":
        break
    else:
        Model_MemoryShort.append({"role":"user", "content":User_input})
        User_talkToModel = True

    # model stuff
    while User_talkToModel == True:
        response = Model_API.chat.completions.create(
            model="localhost",
            messages=Model_MemoryShort, tools=Model_AvailableTools,
            stream=True, tool_choice="auto"
        )
        
        Model_output_type = "none"
        Model_output = ["", "", []] # normal | reasoning | tool

        for chunk in response:
            output_delta = chunk.choices[0].delta
            #print("\t", output_delta) # debug
            Model_output_print = ""

            if getattr(output_delta, "reasoning_content", None):
                if Model_output_type != "reasoning":
                    print("\n*> ", end=""); Model_output_type = "reasoning"

                Model_output[1] += getattr(output_delta, "reasoning_content")
                Model_output_print = getattr(output_delta, "reasoning_content")

            elif output_delta.tool_calls:
                if Model_output_type != "tool":
                    print("\n", end=""); Model_output_type = "tool"

                for tool in output_delta.tool_calls:
                    #print(tool) # debug
                    if tool.id:
                        Model_output[2].append(
                            {
                                "id":tool.id, "type":"function", "function":{
                                    "name":tool.function.name, "arguments":tool.function.arguments
                                }
                            }
                        )
                        Model_output_print = f"\nused tool : {tool.function.name}, {tool.function.arguments}"
                    else:
                        Model_output[2][tool.index]["function"]["arguments"] += tool.function.arguments
                        Model_output_print = tool.function.arguments

            elif output_delta.content:
                if Model_output_type != "normal":
                    print("\nA> ", end=""); Model_output_type = "normal"

                Model_output[0] += output_delta.content or ""
                Model_output_print = output_delta.content or ""

            if Model_output_print != "":
                print(Model_output_print, end="", flush=True)

        print("\n", end="");

        # save for next convo
        Model_MemoryShort.append({"role":"assistant", "content":Model_output[0], "tool_calls":Model_output[2]})

        for tool in Model_output[2]:
            func_arg = json.loads(tool["function"]["arguments"])
            func_result = Model_AvailableTools_Func[tool["function"]["name"]](**func_arg)
            Model_MemoryShort.append({"role":"tool", "tool_call_id":tool["id"], "content":func_result})

        ## auto delete history is deleted ( for now ) so max context is the only one can stop it :V

        if len(Model_output[2]) == 0: ## if there is tool call then keep continue
            break 
