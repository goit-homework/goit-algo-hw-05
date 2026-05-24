"""
Бенчмарк трьох алгоритмів пошуку підрядка на двох статтях.

Для кожного тексту тестуємо два типи паттернів:
  - existing — реально присутній у тексті;
  - missing  — вигаданий, гарантовано відсутній.

Час міряємо через timeit. Перед заміром робимо warmup, щоб збити
артефакти першого запуску. Результат — ASCII-таблиця в консоль і
графік benchmark.png.
"""

import timeit
from pathlib import Path

import matplotlib.pyplot as plt

from algorithms import ALGORITHMS, ALL, BASELINES


HERE = Path(__file__).parent

ARTICLES = {
    "article 1": HERE / "article_1.txt",
    "article 2": HERE / "article_2.txt",
}

# паттерни підбирав уважно: existing береться з тіла відповідної статті,
# missing — однаковий для обох, явно вигаданий рядок
PATTERNS = {
    "article 1": {
        "existing": "алгоритм",
        "missing":  "квантовий_суперкомпʼютер_2077",
    },
    "article 2": {
        "existing": "рекомендац",
        "missing":  "квантовий_суперкомпʼютер_2077",
    },
}

REPEATS = 200  # стільки разів запускаємо кожну комбінацію


def load_articles() -> dict[str, str]:
    texts = {}
    for name, path in ARTICLES.items():
        if not path.exists():
            raise FileNotFoundError(f"не знайдено {path}")
        texts[name] = path.read_text(encoding="utf-8")
    return texts


def sanity_check(text: str, pattern: str, expected_found: bool) -> int:
    """Перевіряємо що всі алгоритми (включно з baselines) дають однакову відповідь."""
    indices = {name: fn(text, pattern) for name, fn in ALL.items()}

    unique = set(indices.values())
    if len(unique) != 1:
        raise AssertionError(
            f"алгоритми не сходяться на паттерні {pattern!r}: {indices}"
        )

    idx = indices["Boyer-Moore"]
    if expected_found and idx < 0:
        raise AssertionError(f"очікувано що {pattern!r} знайдено, а нема")
    if not expected_found and idx != -1:
        raise AssertionError(f"очікувано що {pattern!r} немає, а є на {idx}")

    return idx


def measure(text: str, pattern: str) -> dict[str, float]:
    """Повертає {algo_name: середній час одного запуску в секундах}."""
    timings = {}
    for name, fn in ALL.items():
        # warmup
        fn(text, pattern)
        timer = timeit.Timer(lambda f=fn: f(text, pattern))
        total = timer.timeit(number=REPEATS)
        timings[name] = total / REPEATS
    return timings


def fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:>9.3f} ms"


def print_table(results: dict) -> None:
    print()
    width = 110
    print("=" * width)
    print("  Час пошуку (мс, менше — краще). REPEATS =", REPEATS)
    print("  Колонки 1-3 — власні реалізації; 4-5 — нативні C-baselines зі stdlib.")
    print("=" * width)

    all_names = list(ALL.keys())
    header = f"  {'article':<10} {'pattern':<9}" + "".join(f"{a:>14}" for a in all_names) + "  winner"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for article in ARTICLES:
        for kind in ["existing", "missing"]:
            times = results[article][kind]
            winner = min(times, key=times.get)
            row = f"  {article:<10} {kind:<9}"
            for a in all_names:
                marker = "*" if a == winner else " "
                row += f"  {marker}{times[a] * 1000:>9.3f}ms"
            row += f"  {winner}"
            print(row)
        print()


def plot_results(results: dict, filename: str = "benchmark.png") -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    all_names = list(ALL.keys())

    for ax, article in zip(axes, ARTICLES):
        x_pos = range(len(all_names))
        width = 0.35

        existing_ms = [results[article]["existing"][a] * 1000 for a in all_names]
        missing_ms = [results[article]["missing"][a] * 1000 for a in all_names]

        ax.bar(
            [p - width / 2 for p in x_pos], existing_ms, width,
            label="existing", color="#2e7d32",
        )
        ax.bar(
            [p + width / 2 for p in x_pos], missing_ms, width,
            label="missing", color="#c62828",
        )

        # вертикальна риска що відокремлює власні від baseline
        ax.axvline(len(ALGORITHMS) - 0.5, color="gray", linestyle="--", alpha=0.4)
        ax.text(
            len(ALGORITHMS) - 0.5, ax.get_ylim()[1] * 0.95,
            "  C baselines  ", color="gray", fontsize=9, va="top",
        )

        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(all_names, rotation=15)
        ax.set_ylabel("час, мс")
        ax.set_yscale("log")  # лог-шкала, бо різниця між Python і C — на порядки
        ax.set_title(article)
        ax.grid(True, axis="y", which="both", alpha=0.3)
        ax.legend()

    fig.suptitle("Substring search: Python vs C baselines (log scale)", fontsize=14)
    fig.tight_layout()
    fig.savefig(filename, dpi=120)
    print(f"графік збережено: {filename}")


def main() -> None:
    texts = load_articles()

    print("Перевірка коректності алгоритмів...")
    for article, text in texts.items():
        for kind, pattern in PATTERNS[article].items():
            idx = sanity_check(text, pattern, expected_found=(kind == "existing"))
            status = f"знайдено на позиції {idx}" if idx >= 0 else "не знайдено"
            print(f"  [{article}] [{kind:<8}] {pattern!r:35} -> {status}")
    print()

    print(f"Запуск бенчмарку (REPEATS = {REPEATS} на кожну комбінацію)...")
    results: dict[str, dict[str, dict[str, float]]] = {}
    for article, text in texts.items():
        results[article] = {}
        for kind, pattern in PATTERNS[article].items():
            results[article][kind] = measure(text, pattern)

    print_table(results)
    plot_results(results)


if __name__ == "__main__":
    main()
