"""This package anonymously pulls images from a Docker Registry.

TODO(user): support authenticated pulls.
"""



import argparse
import tarfile

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_image as v2_image
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import save
from containerregistry.client.v2_2 import v2_compat
from containerregistry.transport import transport_pool

import httplib2


parser = argparse.ArgumentParser(
    description='Pull images from a Docker Registry.')

parser.add_argument('--name', action='store',
                    help=('The name of the docker image to pull and save. '
                          'Supports fully-qualified tag or digest references.'))

parser.add_argument('--tarball', action='store',
                    help='Where to save the image tarball.')

_DEFAULT_TAG = 'i-was-a-digest'


# Today save.tarball expects a tag, which is emitted into one or more files
# in the resulting tarball.  If we don't translate the digest into a tag then
# the tarball format leaves us no good way to represent this information and
# folks are left having to tag the resulting image ID (yuck).  As a datapoint
# `docker save -o /tmp/foo.tar bar@sha256:deadbeef` omits the v1 "repositories"
# file and emits `null` for the `RepoTags` key in "manifest.json".  By doing
# this we leave a trivial breadcrumb of what the image was named (and the digest
# is recoverable once the image is loaded), which is a strictly better UX IMO.
# We do not need to worry about collisions by doing this here because this tool
# only packages a single image, so this is preferable to doing something similar
# in save.py itself.
def _make_tag_if_digest(
    name
):
  if isinstance(name, docker_name.Tag):
    return name
  return docker_name.Tag('{registry}/{repository}:{tag}'.format(
      registry=name.registry, repository=name.repository,
      tag=_DEFAULT_TAG))


def main():
  args = parser.parse_args()

  creds = docker_creds.Anonymous()
  transport = transport_pool.Http(httplib2.Http, size=8)

  if '@' in args.name:
    name = docker_name.Digest(args.name)
  else:
    name = docker_name.Tag(args.name)

  with tarfile.open(name=args.tarball, mode='w') as tar:
    with v2_2_image.FromRegistry(name, creds, transport) as v2_2_img:
      if v2_2_img.exists():
        save.tarball(_make_tag_if_digest(name), v2_2_img, tar)
        return

    with v2_image.FromRegistry(name, creds, transport) as v2_img:
      with v2_compat.V22FromV2(v2_img) as v2_2_img:
        save.tarball(_make_tag_if_digest(name), v2_2_img, tar)
        return


if __name__ == '__main__':
  main()
