'''def Even_Odd(number):
    ##result = f"{number} is Even" if number%2==0 else  f"{number} is Odd"
    result = f"{number} is Even" if number & 1==0 else  f"{number} is Odd"
    return result

number=int(input("Enter number:"))
result=Even_Odd(number)
print(result)'''

def Even_Odd(number):
    ##result = (lambda number: f"{number} is Even" if number % 2 == 0 else f"{number} is Odd")(number)
    result = (lambda number: f"{number} is Even" if number & 1 == 0 else f"{number} is Odd")(number)
    return result

number=int(input("Enter number:"))
result=Even_Odd(number)
print(result)

