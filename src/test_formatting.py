def badly_formatted_function(x, y):
    """This is a badly formatted function"""
    result = x + y
    if result > 10:
        print("Result is greater than 10")
    else:
        print("Result is less than or equal to 10")
    return result


def another_bad_function(a, b, c):
    """Another badly formatted function with too many spaces and bad formatting"""
    for i in range(a):
        if i % 2 == 0:
            print(f"Processing {i}")
            result = b * c
        else:
            result = b + c
    return result


if __name__ == "__main__":
    badly_formatted_function(5, 10)
    another_bad_function(3, 4, 5)
