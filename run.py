from mqtt2timescale.__main__ import main as server_main
from utils.env_loader import env_loader


if __name__ == "__main__":
    args = env_loader()

    if args.debug:
        import pydevd_pycharm
        from time import sleep
        # Wait for debug server
        while True:
            try:
                pydevd_pycharm.settrace(args.debug_address, port=2376, stdoutToServer=True, stderrToServer=True)
                break
            except:
                sleep(1)

    server_main(args)
