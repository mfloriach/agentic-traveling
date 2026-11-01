from feed.pipeline import Pipeline


def main() -> None:
    pipeline = Pipeline()
    pipeline.run("./samples")


if __name__ == "__main__":
    main()
