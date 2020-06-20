from pca.data.dao import InMemoryDao
from pca.interfaces.dao import IDao
from pca.utils.dependency_injection import Container


container = Container()
container.register_by_interface(IDao, InMemoryDao)
