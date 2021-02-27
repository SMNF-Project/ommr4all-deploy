from subprocess import check_call
import shutil
import os
import argparse

this_dir = os.path.dirname(os.path.realpath(__file__))
venv = os.path.abspath(os.path.join('/opt', 'ommr4all', 'ommr4all-deploy-venv'))
python = os.path.join(venv, 'bin', 'python')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu', action='store_true')
    parser.add_argument("--dbdir")
    parser.add_argument("--client", action='store_true')
    parser.add_argument("--venv", action='store_true')
    parser.add_argument("--server", action='store_true')
    parser.add_argument("--submodules", action='store_true')
    parser.add_argument("--submodules_bleedingedge", action='store_true')
    parser.add_argument("--calamari", action='store_true')
    parser.add_argument("--serversettings", action='store_true')
    parser.add_argument("--staticfiles", action='store_true')
    parser.add_argument("--migrations", action='store_true')

    args = parser.parse_args()

    os.chdir(this_dir)

    # setup python3 venv for server testing
    check_call(['virtualenv',  '-p', 'python3', venv])

    # run test script inside the venv
    check_call([python, os.path.join(this_dir, 'deploy', 'run_deploy.py')] +
               (['--gpu'] if args.gpu else []) +
               (['--dbdir', args.dbdir] if args.dbdir else []) +
               (['--client'] if args.client else []) +
               (['--venv'] if args.venv else []) +
               (['--server'] if args.server else []) +
               (['--submodules'] if args.submodules else []) +
               (['--submodules_bleedingedge'] if args.submodules_bleedingedge else []) +
               (['--calamari'] if args.calamari else []) +
               (['--serversettings'] if args.serversettings else []) +
               (['--staticfiles'] if args.staticfiles else []) +
               (['--migrations'] if args.migrations else [])
               )


if __name__ == "__main__":
    main()