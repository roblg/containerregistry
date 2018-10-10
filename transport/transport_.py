import httplib2
import logging

DEFAULT_SOURCE_TRANSPORT_CALLABLE = httplib2.Http

class Factory(object):
  """A factory for creating httplib2.Http client instance."""

  def __init__(self, http_callable_transport = DEFAULT_SOURCE_TRANSPORT_CALLABLE):
    self.kwargs = {}
    self.http_callable_transport = http_callable_transport

  def WithCaCert(self, ca_certs):
    self.kwargs['ca_certs'] = ca_certs
    logging.info('Adding CA certificates of %s', ca_certs)
    return self

  def Build(self):
    """Returns a httplib2.Http client constructed with the given values.
    """
    return self.http_callable_transport(**self.kwargs)