def swap(a,b):
   ## a,b = b,a
    a=a * b
    b=a//b
    a=a//b

    return a,b
a=int(input("Enter first number: "))
b=int(input("Enter second number: "))
a,b=swap(a,b)
print("Numbers afte swapping: ",a,b)

'''def swap(a,b):
    a=a^b
    b=a^b
    a=a^b
    a=a+b
    b=a-b
    a=a-b
    return a,b

a=int(input("Enter first number: "))
b=int(input("Enter second number: "))
a,b=swap(a,b)
print("Numbers afte swapping: ",a,b)'''