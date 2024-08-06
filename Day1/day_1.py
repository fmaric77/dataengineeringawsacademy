import json
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



#2


# with open('Day1/task_1.txt', 'r') as file:
#     months = [line.strip() for line in file.readlines()]

# logger.info(months)




#3


# with open('Day1/task_1.txt', 'r') as file:
#     months = [line.strip() for line in file.readlines()]

# months_string = ', '.join(months)
# logger.info(months_string)


#4



# def get_months_string(file_path):
#     with open(file_path, 'r') as file:
#         months = [line.strip() for line in file.readlines()]
#     return ', '.join(months)

# months_string = get_months_string('Day1/task_1.txt')
# logger.info(months_string)



#5




# mixed_list = [
#         1,
#         "February",
#         "March",
#         4.0,
#         "May",
#         "June",
#         "July",
#         "8",
#         "September",
#         "October",
#         "November",
#         "12.5",
#     ]

# concatenated_string = ', '.join(map(str, mixed_list))
# logger.info(concatenated_string)




#6





# def validate_list(mixed_list):
#     valid_months = [
#         "January", "February", "March", "April", "May", "June",
#         "July", "August", "September", "October", "November", "December"
#     ]
    
#     for item in mixed_list:
#         if isinstance(item, (int, float)):
#             if not (1 <= item <= 12 and item == int(item)):
#                 raise ValueError(f"Numeric item {item} is not in the range [1, 12]")
#         elif isinstance(item, str):
#             if item not in valid_months:
#                 raise ValueError(f"Alphabetic item '{item}' is not a valid month name")
#         else:
#             raise ValueError(f"Item '{item}' is neither numeric nor alphabetic")

# mixed_list = [
#     1,
#     "February",
#     "March",
#     4.0,
#     "May",
#     "June",
#     "July",
#     "8",
#     "September",
#     "October",
#     "November",
#     "12.5",
# ]

# validate_list(mixed_list)

# concatenated_string = ', '.join(map(str, mixed_list))
# logger.info(concatenated_string)




#7





# def get_month_name(month_number):
#     month_switch = {
#         1: "January",
#         2: "February",
#         3: "March",
#         4: "April",
#         5: "May",
#         6: "June",
#         7: "July",
#         8: "August",
#         9: "September",
#         10: "October",
#         11: "November",
#         12: "December"
#     }
#     return month_switch.get(month_number, "Invalid month number")

# def get_month_number(month_name):
#     month_switch = {
#         "January": 1,
#         "February": 2,
#         "March": 3,
#         "April": 4,
#         "May": 5,
#         "June": 6,
#         "July": 7,
#         "August": 8,
#         "September": 9,
#         "October": 10,
#         "November": 11,
#         "December": 12
#     }
#     return month_switch.get(month_name, "Invalid month name")

# logger.info(get_month_name(1))  
# logger.info(get_month_number("January"))






#8





# mixed_list = [
#     1,
#     "February",
#     "March",
#     4.0,
#     "May",
#     "June",
#     "July",
#     "8",
#     "September",
#     "October",
#     "November",
#     "12",
# ]

# month_names = [
#     "January", "February", "March", "April", "May", "June",
#     "July", "August", "September", "October", "November", "December"
# ]

# months_dict_list = []

# for item in mixed_list:
#     if isinstance(item, (int, float)) or (isinstance(item, str) and item.isdigit()):
#         month_number = int(float(item))
#         if 1 <= month_number <= 12:
#             month_dict = {
#                 "name": month_names[month_number - 1],
#                 "number": month_number
#             }
#             months_dict_list.append(month_dict)
#     else:
#         if item in month_names:
#             month_number = month_names.index(item) + 1
#             month_dict = {
#                 "name": item,
#                 "number": month_number
#             }
#             months_dict_list.append(month_dict)

# logger.info(months_dict_list)




#9




# months_dict_list = [
#     {"name": "January", "number": 1},
#     {"name": "February", "number": 2},
#     {"name": "March", "number": 3},
#     {"name": "April", "number": 4},
#     {"name": "May", "number": 5},
#     {"name": "June", "number": 6},
#     {"name": "July", "number": 7},
#     {"name": "August", "number": 8},
#     {"name": "September", "number": 9},
#     {"name": "October", "number": 10},
#     {"name": "November", "number": 11},
#     {"name": "December", "number": 12}
# ]

# with open('day_2.json', 'w') as file:
#     json.dump(months_dict_list[:6], file, indent=4)

# with open('day_2.json', 'r+') as file:
#     data = json.load(file)
#     data.extend(months_dict_list[-4:])
#     file.seek(0)
#     json.dump(data, file, indent=4)

# with open('day_2.json', 'r') as file:
#     data = json.load(file)
#     logger.info(data)
#     logger.info(f"Length of the list: {len(data)}")



   