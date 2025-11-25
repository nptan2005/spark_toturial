import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.padding import PKCS7
from ..utilities.utils import Utils as utils


class encoder:

    def __init__(self, masterKey:bytes = None , key: bytes = None , iv: bytes = None  ):
        self.__master_key = masterKey
        self.__key = key
        self.__iv = iv
        self.__enKey = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__master_key = None
        self.__key = None
        self.__iv = None

    def __del__(self):
        del self.__master_key, self.__key, self.__iv 

    @property
    def AESEncryptKey(self):
        return self.__enKey
    
    @AESEncryptKey.setter
    def AESEncryptKey(self, value):
        self.__enKey = value

    @property
    def AESKey(self):
        """Clear Client Key"""
        return self.__key
    
    @AESKey.setter
    def AESKey(self, value):
        self.__key = value
    

    @property
    def AESMasterKey(self):
        return self.__master_key
    
    @AESMasterKey.setter
    def AESMasterKey(self, value):
        self.__master_key = value
    
    @property
    def AESIVMasterKey(self):
        return self.__iv
    
    @AESIVMasterKey.setter
    def AESIVMasterKey(self, value):
        self.__iv = value

    ####################################################################
    ##### Private func: internal process
    ####################################################################
    # input -> value
    # key = b'your_secret_key'  # Thay bằng khóa AES (32 byte)
    # iv = os.urandom(16)  # Tạo vector khởi tạo ngẫu nhiên (16 byte) => IV (Initialization Vector)
    #######################################################################################
    # cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(iv)), backend=default_backend()): Tạo một đối tượng mã hóa Cipher với các tham số:
    # algorithms.AES(key): Xác định thuật toán mã hóa là AES với khóa key đã cho.
    # modes.CBC(bytes(iv)): Xác định chế độ mã hóa là CBC với vector khởi tạo (IV) iv.
    # backend=default_backend(): Chỉ định backend mặc định cho mã hóa, thường là default_backend() được cung cấp bởi thư viện cryptography.
    # encryptor = cipher.encryptor(): Tạo một đối tượng encryptor để thực hiện mã hóa.
    # padder = PKCS7(algorithms.AES.block_size).padder(): Tạo một đối tượng padder để thực hiện padding PKCS7.
    # PKCS7(algorithms.AES.block_size): Xác định phương thức padding là PKCS7 với độ dài khối (block size) của AES là 16 byte.
    # padded_data = padder.update(value) + padder.finalize(): Thực hiện padding cho dữ liệu đã cho.
    # padder.update(value): Thực hiện padding cho phần dữ liệu đã cho.
    # padder.finalize(): Hoàn thành quá trình padding và thêm các byte padding còn lại.
    # return encryptor.update(padded_data) + encryptor.finalize(): Mã hóa dữ liệu đã được padding và trả về chuỗi mã hóa.
    # encryptor.update(padded_data): Mã hóa một phần dữ liệu đã được padding.
    # encryptor.finalize(): Hoàn thành quá trình mã hóa và trả về chuỗi mã hóa.

    def AESEncrypt(self, value: bytes, key: bytes, iv: bytes) -> bytes:
        """Giải mã chuỗi văn bản đã được mã hóa bằng AES."""

        cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(iv)), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(value) + padder.finalize()
        return encryptor.update(padded_data) + encryptor.finalize()



    def AESEncryptKey(self, key:bytes, iv:bytes):
        """Encrypt any key by Master key; not use this func for first step 'setup key
        """
        return self.AESEncrypt(key, self.__master_key, iv)
    

    def AESEncryptDataByKey(self, value, key:bytes, iv:bytes):
        """Encrypt value by any key
            if value is str ==> return base64
            if value is bytes ==> return bytes
            else return None
        """
        __typeOfValue = utils.checkTypeOfValue(value)

        __value = None
        if __typeOfValue == "str":
            __value = utils.convertStrToBytes(value)
        else:
            __value = value

        __data = self.AESEncrypt(__value, key, iv)

        if __typeOfValue == "str":
            return utils.convertBytesToBase64(__data)
        elif __typeOfValue == "bytes":
            return __data
        return None


    def AESEncryptDataToFile(self, value:str, key:bytes, dataPath:str,ivPath:str, iv:bytes = None) -> tuple[str, str]:
        """Encryt Value by application key
            Default: encrypt Data alway save on this app
            if path is not None, file also save to path
            --
            func return value, iv
            * Note: if iv = None, application with generate it
                    iv return base64, file save bytes type
            * value:
                value return base64
                file save bytes
        """
        ## check value
        if value is None or dataPath is None or ivPath is None:
            return None, None
        
        ## gen iv
        __iv = None
        if iv is None:
            __iv = os.urandom(16)
        else:
            __iv = iv


        
        ## encryt Data

        __valueBytes = utils.convertStrToBytes(value)

        __encryptData = self.AESEncryptDataByKey(__valueBytes, key, __iv)

        ## save data to file
        ##### Save to default path
        utils.writeFile(__iv, ivPath, "wb")
        utils.writeFile(__encryptData, dataPath, "wb")

        ### return value
        return utils.convertBytesToBase64(__encryptData), utils.convertBytesToBase64(__iv)


    
    


    