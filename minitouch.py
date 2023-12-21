def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def find_primes_below_n(n):
    prime_list = [2]
    for num in range(3, n):
        if is_prime(num):
            prime_list.append(num)
    return prime_list


try:
    n = int(input("请输入一个整数: "))
    if n <= 0:
        print("请输入一个大于0的整数。")
    else:
        primes = find_primes_below_n(n)
        print(f"{n}以下的素数: {primes}")
except ValueError:
    print("无效输入，请输入一个整数。")
