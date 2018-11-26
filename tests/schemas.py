from jsonschema import validate
import json


message_schema = {
  "$schema": "http://json-schema.org/draft-04/schema#",  
  "type": "object",
    "properties": { 
          "properties":{
            "ok": {"type": "boolean"},
            "result": {
                "type": "object",
                "properties":{
                    "message_id": {"type": "number"},
                    "from": {
                        "properties":{
                            "id": {"type": "number"},
                            "is_bot": {"type": "boolean"},
                            "first_name": {"type": "string"},
                            "username": {"type": "string"}                                                       
                        },
                        "required": ["id", "is_bot", "first_name", "username"]
                    },
                    "chat": {
                        "properties":{
                            "id": {"type": "number"},
                            "first_name": {"type": "string"},                            
                            "username": {"type": "string"},
                            "type": {"type": "string"}
                        },
                        "required": ["id", "firs_name", "username", "type"]
                    },
                    "date": {"type": "number"},
                    "text": {"type": "string"},
                    "entities":{
                        "type": "array",
                        "properties":{
                            "offset": {"type": "number"},
                            "length": {"type": "number"},
                            "type": {"type": "string"}
                        },
                        "required": ["offset", "length", "type"]
                    }
                },
                "required": ["message_id", "from", "chat", "date", "text", "entities"]
            }
          },          
          "required": ["ok", "result"]
    }  
}

no_message_schema = {
  "$schema": "http://json-schema.org/draft-04/schema#",  
  "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "result": {
            "type": "array",                
        }
    },          
    "required": ["ok", "result"]
}  



def assert_valid_schema(data, schema):
    """ Checks whether the given data matches the schema """    
    return validate(data, schema)