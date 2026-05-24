"""
Три класичних алгоритми пошуку підрядка, реалізовані з нуля,
плюс два baseline на C (str.find і re.search зі stdlib).

Усі повертають індекс першого входження або -1, якщо не знайдено.
Інтерфейс: search(text: str, pattern: str) -> int
"""

import re


def boyer_moore_search(text: str, pattern: str) -> int:
    """
    Boyer-Moore (спрощена версія, тільки bad-character).

    Ідея: ідемо по паттерну справа наліво. Якщо символ не співпав,
    зсуваємо паттерн так, щоб поганий символ опинився під своїм
    найправішим входженням у паттерні.
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return 0
    if m > n:
        return -1

    # для кожного символу — його найправіший індекс у патерні
    bad_char = {ch: i for i, ch in enumerate(pattern)}

    i = 0
    while i <= n - m:
        j = m - 1
        while j >= 0 and pattern[j] == text[i + j]:
            j -= 1
        if j < 0:
            return i
        # зсуваємо мінімум на 1 (інакше зациклимось)
        shift = j - bad_char.get(text[i + j], -1)
        i += max(1, shift)

    return -1


def _kmp_failure_table(pattern: str) -> list[int]:
    """Префікс-функція: fail[i] = довжина найдовшого власного префікс-суфікса
    для pattern[:i+1]."""
    fail = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k > 0 and pattern[k] != pattern[i]:
            k = fail[k - 1]
        if pattern[k] == pattern[i]:
            k += 1
        fail[i] = k
    return fail


def kmp_search(text: str, pattern: str) -> int:
    """
    Knuth-Morris-Pratt.

    Префіксна функція дозволяє не повертатися по тексту: при невдалому
    збігу зсуваємо паттерн на відому довжину префікс-суфікса.
    """
    if not pattern:
        return 0

    fail = _kmp_failure_table(pattern)
    j = 0
    for i, ch in enumerate(text):
        while j > 0 and pattern[j] != ch:
            j = fail[j - 1]
        if pattern[j] == ch:
            j += 1
            if j == len(pattern):
                return i - j + 1
    return -1


def rabin_karp_search(
    text: str,
    pattern: str,
    base: int = 257,
    mod: int = 10**9 + 7,
) -> int:
    """
    Rabin-Karp з rolling hash.

    Хешуємо паттерн і кожне вікно тексту тієї ж довжини. Якщо хеші
    рівні — на всякий випадок порівнюємо явно (захист від колізій).
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return 0
    if m > n:
        return -1

    # base^(m-1) mod mod — для викидання старшого символа з вікна
    high_power = pow(base, m - 1, mod)

    pat_hash = 0
    win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * base + ord(pattern[i])) % mod
        win_hash = (win_hash * base + ord(text[i])) % mod

    for i in range(n - m + 1):
        if pat_hash == win_hash and text[i:i + m] == pattern:
            return i
        if i < n - m:
            win_hash = (
                (win_hash - ord(text[i]) * high_power) * base
                + ord(text[i + m])
            ) % mod

    return -1


def str_find_search(text: str, pattern: str) -> int:
    """Нативний str.find() — внутрішньо реалізований на C у CPython
    (two-way string matching). Baseline для порівняння."""
    return text.find(pattern)


def re_search(text: str, pattern: str) -> int:
    """re.search() з екранованим паттерном. Регулярки в C, з повним
    NFA-двигуном — навіть на простому пошуку є оверхед на компіляцію
    та матчер, але це теж native code."""
    match = re.search(re.escape(pattern), text)
    return match.start() if match else -1


# власні реалізації — основна частина завдання
ALGORITHMS = {
    "Boyer-Moore": boyer_moore_search,
    "KMP":         kmp_search,
    "Rabin-Karp":  rabin_karp_search,
}

# C-baselines для контексту: наскільки далеко від нативу наш Python
BASELINES = {
    "str.find()": str_find_search,
    "re.search()": re_search,
}

ALL = {**ALGORITHMS, **BASELINES}

