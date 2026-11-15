Model_AvailableTools = []; Model_AvailableTools_Func = {}
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

## put tools here
@Model_Tool(
    "reverse text from back to front", 
    text={"type":"string", "desc":"put the text that want be reversed here", "required":True}
)
def reverse_text(text:str):
    return text[::-1]