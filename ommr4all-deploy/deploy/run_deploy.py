from subprocess import check_call, call
import os
import re
from distutils.dir_util import copy_tree
import shutil
import sys
import logging
import argparse

logger = logging.getLogger(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(this_dir, '..', '..'))
ommr4all_dir = '/opt/ommr4all'
storage_dir = os.path.join(ommr4all_dir, 'storage')
db_file_name = 'db.sqlite'
secret_key = os.path.join(ommr4all_dir, '.secret_key')
python = sys.executable
pip = os.path.join(os.path.dirname(python), 'pip')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbdir", default=ommr4all_dir)
    parser.add_argument("--gpu", action='store_true')
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

    db_file = os.path.join(args.dbdir, db_file_name)

    os.chdir(root_dir)


    if args.client:
        print("\n\n\n======== run_deploy.py: Setting up client ====", file=sys.stderr)
        logger.info("Setting up client")
        os.chdir('modules/ommr4all-client')
        check_call(['sed', '-i', '-e', 's#routerLink="/imprint"#href="https://www.uni-wuerzburg.de/en/sonstiges/imprint-privacy-policy/"#g', 'src/app/app.component.html'])
        check_call(['npm', 'install'])
        check_call(['npm', 'audit', 'fix', '--audit-level', 'high'])
        for config in ['production', 'production-de']:
            check_call(['ng', 'build', '--configuration', config])


    if args.venv:
        print("\n\n\n\n\n============= run_deploy.py: setting up virtual environment and dependencies =========\n\n\n", file=sys.stderr)
        logger.info("Setting up virtual environment and dependencies")
        os.chdir(root_dir)

        print("\n\n\n======== run_deploy.py: Installing tensorflow ====", file=sys.stderr)
        # There is impending dependency hell when absl-py is not manually set to lower version
        check_call([pip, 'install', 'absl-py<0.11,>=0.9'])

        check_call([pip, 'install', 'tensorflow_gpu>=2.0' if args.gpu else 'tensorflow>=2.0'])


    if args.server:
        print("\n\n\n======== run_deploy.py: Installing ommr4all-server requirements ====", file=sys.stderr)
        os.chdir('modules/ommr4all-server')
        if args.submodules_bleedingedge:
            check_call(['git', 'pull', 'origin', 'master'])
            check_call(['git', 'checkout', 'master'])
        check_call([pip, 'install', '-r', 'requirements.txt'])
        os.chdir(root_dir)


    if args.submodules:
        for submodule in ['ommr4all-page-segmentation', 'ommr4all-line-detection', 'ommr4all-layout-analysis']:
            print("\n\n\n======== run_deploy.py: Installing submodule {} ====".format(submodule), file=sys.stderr)
            os.chdir('modules/' + submodule)
            if args.submodules_bleedingedge:
                check_call(['git', 'pull', 'origin', 'master'])
                check_call(['git', 'checkout', 'master'])
            check_call([python, 'setup.py', 'install'])
            os.chdir(root_dir)


    if args.calamari:
        # Install calamari without git pull
        os.chdir('modules/calamari')
        check_call([python, 'setup.py', 'install'])
        os.chdir(root_dir)


    os.chdir(root_dir)
    os.makedirs(storage_dir, exist_ok=True)


    if args.serversettings:
        print("\n\n\n\n\n============= run_deploy.py: changing server settings =========\n\n\n", file=sys.stderr)
        logger.info("Changing server settings")
        os.chdir('modules/ommr4all-server')

        # create/read secret key
        if not os.path.exists(secret_key):
            from django.core.management import utils
            with open(secret_key, 'w') as f:
                f.write(utils.get_random_secret_key())

        with open(secret_key, 'r') as f:
            random_secret_key = f.read()

        with open('ommr4all/settings.py', 'r') as f:
            settings = f.read()

        settings = settings.replace('ALLOWED_HOSTS = []', 'ALLOWED_HOSTS = ["*"]')
        settings = settings.replace('DEBUG = True', 'DEBUG = False')
        settings = settings.replace('db.sqlite', '{}'.format(db_file))
        settings = settings.replace("BASE_DIR, 'storage'", "'{}'".format(storage_dir))
        settings = re.sub(r"SECRET_KEY = .*", "SECRET_KEY = '{}'".format(random_secret_key), settings)

        with open('ommr4all/settings.py', 'w') as f:
            f.write(settings)
        os.chdir(root_dir)


    if args.staticfiles:
        print("\n\n\n\n\n============= run_deploy.py: Collecting static files =========\n\n\n", file=sys.stderr)
        logger.info("Collecting static files")
        os.chdir('modules/ommr4all-server')
        check_call([python, 'manage.py', 'collectstatic', '--noinput'])
        os.chdir(root_dir)


    if args.migrations:
        print("\n\n\n\n\n============= run_deploy.py: Migrating database and copying new version =========\n\n\n", file=sys.stderr)
        logger.info("Migrating database and copying new version")
        os.chdir('modules/ommr4all-server')

        call(['/usr/sbin/service', 'apache2', 'stop'])

        # backup files
        copy_tree(storage_dir, storage_dir + '.backup')
        shutil.rmtree(db_file + '.backup', ignore_errors=True)
        if os.path.exists(db_file):
            shutil.copyfile(db_file, db_file + '.backup')

        check_call([python, 'manage.py', 'migrate'])

        # copy new version and remove all
        os.chdir(root_dir)
        shutil.rmtree(os.path.join(ommr4all_dir, 'ommr4all-deploy'), ignore_errors=True)
        copy_tree(root_dir, os.path.join(ommr4all_dir, 'ommr4all-deploy'))

        # finally restart the service
        call(['/usr/sbin/service', 'apache2', 'start'])
        logger.info("Setup finished")
        os.chdir(root_dir)


if __name__ == "__main__":
    main()
