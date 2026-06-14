def collect_answers(fields):
    answer = {}
    for field in fields:
        print(field["prompt"])
        if field["kind"] == "choice":
            for key,value in field["options"].items():
                print(f"Press {key} for {value}\n")
            
            response_choice = input("Please enter your choice")
            while response_choice not in field["options"]:
               response_choice = input("Please enter the appropriate choice")

            answer[field["name"]] = field["options"][response_choice] 

        elif field["kind"] == "text":
            response_text = input(">")
            answer[field["name"]] = response_text

        elif field["kind"] == "int":
            response_int = input(">")
            
            while response_int.isdigit() is False:
                response_int = input("Please enter a number")
            
            response_int = int(response_int)

            answer[field["name"]] = response_int

        elif field["kind"] == "list":
            response_list = input("Please use commas to seperate your answers")
            answer[field["name"]] = response_list.split(",")

        elif field["kind"] == "float":

            while True:
                response_float = input("You can use a floating number for this answer")

                try:
                    response_float = float(response_float)
                    break
                except ValueError:
                    print("Please enter a valid floating number")
            
            answer[field["name"]] = response_float

    return answer

            