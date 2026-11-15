from openai import OpenAI
import json

Model_API = OpenAI(base_url="http://localhost:18000/v1", api_key="Localhost")
Model_MemoryShort = [
    {"role":"system", "content":"you are helpful lazy assistant"}
]
Model_AvailableTools = []; Model_AvailableTools_Func = {}

## func to add tool call
def Model_Tool(description:str, **properties):
    """
        **properties

        < func_arg_name >={
            "type":"< string/interger/number/boolean/object/array >"
            "desc":"< desctiption for arg >"
            "required":< boolean >
        } 
    """

    required = []

    def decorator(func):
        for name, info in properties.items():
            if info.get("required", False):
                required.append(name)

        Model_AvailableTools.append(
            {"type":"function", "function":{
                    "name":func.__name__, "description":description, "parameters":{
                        "type":"object", "properties":{
                            name:{"type":info["type"], "description":info["desc"]} for name, info in properties.items()
                        },
                            "required":required
                    }
                }
            }
        )

        Model_AvailableTools_Func[func.__name__] = func

        return func

    return decorator

## tools
@Model_Tool(
    "reverse text from back to front", 
    text={"type":"string", "desc":"put the text that want be reversed here", "required":True}
)
def reverse_text(text:str):
    return text[::-1]

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
    while True:
        response = Model_API.chat.completions.create(
            model="localhost",
            messages=Model_MemoryShort, tools=Model_AvailableTools,
            stream=True, tool_choice="auto"
        )
        
        Model_Action = "normal"
        Model_fullOutput = ""
        Model_tool_call = []
        Model_tool_call_memo = []
        Model_tool_call_result = []
        for chunk in response:
            output_delta = chunk.choices[0].delta
            #print("\t", output_delta) # debug

            if getattr(output_delta, "reasoning_content", None): # clean this area ( could be simpler )
                if Model_Action != "reasoning":
                    print("\n\n*> ", end=""); Model_Action = "reasoning"
                output_content = getattr(output_delta, "reasoning_content")
            elif output_delta.tool_calls:
                if Model_Action != "tool":
                    print("\n\n#> ", end=""); Model_Action = "tool"

                for tool in output_delta.tool_calls:
                    if tool.id:
                        Model_tool_call.append(
                            [tool.id, tool.function.name, tool.function.arguments]
                        )
                    else:
                        Model_tool_call[-1][2] += tool.function.arguments

                #output_content = output_delta.tool_calls
            else:
                if Model_Action != "normal":
                    if Model_Action == "tool": print(Model_tool_call)
                    print("\n\nA> ", end=""); Model_Action = "normal"
                output_content = output_delta.content
            
            if output_content:
                print(output_content, end="", flush=True)
                if Model_Action == "normal": Model_fullOutput += output_content

        print("\n");

        for tool in Model_tool_call:
            temp = {"id":tool[0], "type":"function", "function":{"name":tool[1], "arguments":tool[2]}}
            Model_tool_call_memo.append(temp)
            func_arg = json.loads(temp["function"]["arguments"])
            func_result = Model_AvailableTools_Func[temp["function"]["name"]](**func_arg)
            Model_tool_call_result.append({"role":"tool", "tool_call_id":temp["id"], "content":func_result})

        # save for next convo
        Model_MemoryShort.append({"role":"assistant", "content":Model_fullOutput, "tool_calls":Model_tool_call_memo})
        for i in Model_tool_call_result:
            Model_MemoryShort.append(i)

        if len(Model_MemoryShort) > 50: ## add adaptive delete stuff later
            Model_MemoryShort.pop(1)
        #print(Model_MemoryShort) # debug

        if len(Model_tool_call_result) == 0: ## if there is tool call result then keep continue
            break 
