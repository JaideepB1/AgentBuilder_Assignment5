import json

with open("sweep_results.json") as file:
    sweep = json.load(file)

results = sweep["results"]

lines = [
    "# Dispositions",
    "",
    "| account_id | verdict | confidence | reasoning |",
    "|---|---|---|---|",
]

for result in results:
    reasoning = result["reasoning"].replace("|", "\\|").replace("\n", " ")

    lines.append(
        f'| {result["account_id"]} | '
        f'{result["verdict"]} | '
        f'{result["confidence"]} | '
        f'{reasoning} |'
    )

with open("DISPOSITIONS.md", "w") as file:
    file.write("\n".join(lines))