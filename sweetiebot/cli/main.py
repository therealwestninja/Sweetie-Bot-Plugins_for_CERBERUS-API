
import argparse
from sweetiebot.runtime import SweetieBotRuntime
from sweetiebot.core.loop import SweetieBotLoop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", choices=["start", "stop"])

    args = parser.parse_args()
    runtime = SweetieBotRuntime()
    loop = SweetieBotLoop(runtime)

    if args.loop == "start":
        loop.start()
    elif args.loop == "stop":
        loop.stop()


if __name__ == "__main__":
    main()
