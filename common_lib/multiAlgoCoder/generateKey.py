import os
from .decoder import decoder
from .encoder import encoder
from ..utilities.utils import Utils as utils
import datetime
from pathlib import Path

class configConstant:    
    # default key folder
    ENCODER_FOLDER = Path(__file__).resolve().parent.parent / "bin"
    ENCODER_GEN_FOLDER = "gen"
    ENCODER_KEY_FOLDER = "key"
    ENCODER_IV_FOLDER = "iv"
    ENCODER_DATA_FOLDER = "data"
    # system key name
    MASTER_KEY_NAME = "master_key_ase.bin"
    MASTER_KEY_IV_NAME = "master_key_iv_ase.bin"
    KEY_NAME = "key_ase.bin"

    # other key name
    OTHER_KEY_NAME = "_key_ase.bin"
    OTHER_IV_KEY_NAME = "_iv_key_ase.bin"

    # data encrypt
    ENCRYPTION_KEY_IV_NAME = "encryption_iv.bin"
    ENCRYPTION_CONTENT_FILE = "encryption_data.bin"

class generateKey:
    
    @staticmethod
    def randomKeyWithByteType(length: int = 32) -> bytes:
        """Random AES Key.
            return Bytes
        """
        return os.urandom(length)
    
    @staticmethod
    def randomKeyWithBase64(lenght: int = 32) -> str:
        """Hàm tạo khóa AES ngẫu nhiên.
        return Str
        """
        return utils.convertBytesToBase64(generateKey.randomKeyWithByteType(lenght))
    
    @staticmethod
    def randomKeyWithHex(lenght: int = 32, isFormat: bool = False) -> str:
        """Hàm tạo khóa AES ngẫu nhiên.
            return hex
        """
        if isFormat == False:
            return generateKey.randomKeyWithByteType(lenght).hex()
        
        return utils.hexFormat(generateKey.randomKeyWithByteType(lenght))
    
    @staticmethod
    def randomKeyWithAscii(lenght: int = 32) -> str:
        """Hàm tạo khóa AES ngẫu nhiên.
            return Ascii
        """
        return utils.convertBytesToAscii(generateKey.randomKeyWithByteType(lenght))
    

    
    @staticmethod
    def saveKeyToFile(keyValue, filePath):
        __type = utils.checkTypeOfValue(keyValue)
        __mode = "w"
        if __type == "bytes":
            __mode = "wb"
        
        utils.writeFile(keyValue, filePath, __mode)

    @staticmethod
    def readKeyFromFle(filePath, mode):
        """ Load Key from file
            check type of key
            if key is str: mode = w
            if key is bytes: mode = wb
        """
        return utils.readFile(filePath, mode)
    
    @staticmethod
    def master_key():
        __master_key_file = os.path.join(
                configConstant.ENCODER_FOLDER, configConstant.ENCODER_KEY_FOLDER, configConstant.MASTER_KEY_NAME
            )
        return utils.readFile(__master_key_file, "rb")

    # end load_master_key
    @staticmethod
    def key():
        __key_file = os.path.join(
                configConstant.ENCODER_FOLDER, configConstant.ENCODER_KEY_FOLDER, configConstant.KEY_NAME
            )
        return utils.readFile(__key_file, "rb")
    
    def iv_master_key():
        """Load IV from file"""
        __iv_file = os.path.join(
                configConstant.ENCODER_FOLDER, configConstant.ENCODER_IV_FOLDER, configConstant.MASTER_KEY_IV_NAME
            )
        return utils.readFile(__iv_file, "rb")
    
    @staticmethod
    def generateAESKey4ScheduleService():
        """Gen key for service:
           -- Master Key
           -- IV
           -- client key
        """

        __today = datetime.date.today().strftime("%Y%m%d")
        __master_key_fileName_tmp = os.path.join(
            configConstant.ENCODER_FOLDER,configConstant.ENCODER_GEN_FOLDER, __today + '_' + configConstant.MASTER_KEY_NAME
        )
        ### Step 1: Random Master Key voi 256 bit (32 Bytes)
        __master_key = generateKey.randomKeyWithByteType()
        print('END ### Step 1: Random Master Key voi 256 bit (32 Bytes)')
        ### Step 2: Save hen gen folder
        generateKey.saveKeyToFile(__master_key, __master_key_fileName_tmp)
        print('END ### Step 2: Save hen gen folder')
        ### Step 3: Move Master Key to key folder
        _master_key_file = os.path.join(
            configConstant.ENCODER_FOLDER, configConstant.ENCODER_KEY_FOLDER, configConstant.MASTER_KEY_NAME
        )
        utils.move_and_rename_file(__master_key_fileName_tmp, _master_key_file)
        print('END ### Step 3: Move Master Key to key folder')
        ### Step 4: generate IV (Vector) >> prepare for gen Client Key, IV 16 bytes
        _iv_master_key = generateKey.randomKeyWithByteType(16)
        print('END ### Step 4: generate IV (Vector) >> prepare for gen Client Key, IV 16 bytes')
        ### Step 5: Save IV to iv folder
        _iv_file = os.path.join(
            configConstant.ENCODER_FOLDER, configConstant.ENCODER_IV_FOLDER, configConstant.MASTER_KEY_IV_NAME
        )
        generateKey.saveKeyToFile(_iv_master_key, _iv_file)
        print('END ### Step 5: Save IV to iv folder')
        ### Step 6: generate client key
        __client_key = generateKey.randomKeyWithByteType()
        print('END ### Step 6: generate client key')
        #### Step 7: encrytion client key by master key
        __client_key_encrypt = None
        with encoder() as en:
            __client_key_encrypt = en.AESEncrypt(__client_key, __master_key, _iv_master_key)

        print('END #### Step 7: encrytion client key by master key')
        #### Step 8: Save client key to file
        __client_key_fileName_tmp = os.path.join(
            configConstant.ENCODER_FOLDER,configConstant.ENCODER_GEN_FOLDER, __today + '_' + configConstant.KEY_NAME
        )
        generateKey.saveKeyToFile(__client_key_encrypt, __client_key_fileName_tmp)
        print('step 8: save')
        _key_file = os.path.join(
            configConstant.ENCODER_FOLDER, configConstant.ENCODER_KEY_FOLDER, configConstant.KEY_NAME
        )
        utils.move_and_rename_file(__client_key_fileName_tmp, _key_file)
        print('END #### Step 8: Save client key to file')

    @staticmethod
    def generateAESKey(tabName:str, keyfilePath:str = None, ivfilePath:str = None):
        """Generate any Key (AES), Encrytion key by master key
            keyfilePath: input folder path only, tabName is prefix of file Name, EX: [tabName]__key_ase.bin
            if TabName is None >>> %Y%m%d_%H%M%S
            Default: key file store key folder (None); iv: store iv
            #####
            return encryption key (bytes)
        """
        # Step 1: define key and iv name
        __keyName = None
        __ivName = None
        if tabName is None or tabName == '':
            __today = datetime.date.today().strftime("%Y%m%d_%H%M%S")
            __keyName = __today + configConstant.OTHER_KEY_NAME
            __ivName = __today + configConstant.OTHER_IV_KEY_NAME
        else:
            __keyName = tabName + configConstant.OTHER_KEY_NAME
            __ivName = tabName + configConstant.OTHER_IV_KEY_NAME

        print('### End # Step 1: define key and iv name')

        # Step 2: define path stored key
        __keyPath = None
        if keyfilePath is None or not os.path.exists(keyfilePath):
            __keyPath = os.path.join(
                configConstant.ENCODER_FOLDER, configConstant.ENCODER_KEY_FOLDER, __keyName
            )
        else:
            __keyPath = os.path.join(keyfilePath, __keyName)

        __ivPath = None
        if ivfilePath is None or not os.path.exists(ivfilePath):
            __ivPath = os.path.join(
                configConstant.ENCODER_FOLDER, configConstant.ENCODER_IV_FOLDER, __ivName
            )
        else:
            __ivPath = os.path.join(ivfilePath, __ivName)

        print('### End # Step 2: define path stored key')

        ## Step 3: Gen clear key and iv
        __key_gen = generateKey.randomKeyWithByteType()
        print('#### End Step 3.1 gen clear key')
        __iv_gen = generateKey.randomKeyWithByteType(16)
        print('#### End Step 3.2 gen iv')
        __encrypt_key = None
        # Step 4: Encyption key by Master Key
   
        with encoder(generateKey.master_key(), generateKey.key(), generateKey.iv_master_key()) as en:
            __encrypt_key = en.AESEncryptKey(__key_gen,__iv_gen)
        
        print('### End # Step 4: Encyption key by Master Key')
        ## Step 5: Save encryption key to file
        generateKey.saveKeyToFile(__encrypt_key, __keyPath)
        print(f'### End # Step 5: Save encryption key to file, filePath = {__keyPath}')
        ## Step 5: Save iv to file
        generateKey.saveKeyToFile(__iv_gen, __ivPath)
        print(f'### End # Step 6: Save iv to file, iv filePath = {__ivPath}')
    # end generateAESKey


    @staticmethod
    def getPathFromTabName(tabName:str) -> tuple[str,str]:

        _dataPath = os.path.join(
                configConstant.ENCODER_FOLDER,configConstant.ENCODER_DATA_FOLDER, tabName + '_' + configConstant.ENCRYPTION_CONTENT_FILE)
        
        _ivPath = os.path.join(
                    configConstant.ENCODER_FOLDER,configConstant.ENCODER_IV_FOLDER, tabName + '_' + configConstant.ENCRYPTION_KEY_IV_NAME)
        
        return _dataPath, _ivPath
    # end getPathFromTabName


    @staticmethod
    def decode_key():
        __key = None
        # print(__iv)
        with decoder(generateKey.master_key(), __key, generateKey.iv_master_key()) as de:
            __key = de.AESDecryptKey(generateKey.key())
        return __key

    @staticmethod
    def decode_str(tabName:str) -> str:
            
        __key = generateKey.decode_key()
        # print(f'base64 = {tabName}')
        tab_bytes = utils.convertBase64ToBytes(tabName)
        # print(f'bytes = {tab_bytes}')
        tab_str = tab_bytes.decode("ascii", errors="ignore")
        # print(f'str = {tab_str}')
        _encryptDataPath, _ivPath = generateKey.getPathFromTabName(tab_str)
        with decoder(generateKey.master_key(), __key, generateKey.iv_master_key()) as de:
            # print(de.AESDecryptBase64Data('3N0qO7CXrHxrkB40QEUXiA==', 'uKoA49KyhVJUvyAyxOHvLw=='))
            return de.AESDecryptDataFromFile(_encryptDataPath, _ivPath)
    # end decode_str

    @staticmethod
    def buildPathFromTabName(tabName:str,path:str = None)-> tuple[str,str]:
        ## key file name and filePath
        __fileName = tabName + '_' + configConstant.ENCRYPTION_CONTENT_FILE
        __ivfileName = tabName + '_' + configConstant.ENCRYPTION_KEY_IV_NAME

        if path is not None and utils.checkPathIsDir(path) == True:
            dataPath = os.path.join(path, __fileName)
            ivPath = os.path.join(path, __ivfileName)
            
        else:

            dataPath = os.path.join(
                    configConstant.ENCODER_FOLDER,configConstant.ENCODER_DATA_FOLDER, __fileName)
            
            ivPath = os.path.join(
                        configConstant.ENCODER_FOLDER,configConstant.ENCODER_IV_FOLDER, __ivfileName)
        
        return dataPath, ivPath
    # end buildPathFromTabName

    @staticmethod
    def encode_str(value:str, tab:str) -> str:
        __key = generateKey.decode_key()
        __result = None
        print(f'value = {value}, tab = {tab}')
        dataPath, ivPath = generateKey.buildPathFromTabName(tab)
        with encoder(generateKey.master_key(), __key, generateKey.iv_master_key()) as en:
            a, b = en.AESEncryptDataToFile(value,__key,dataPath,ivPath)
            print(f'encode value = {a}, iv = {b}')

            tab_bytes =  utils.convertStrToBytes(tab)
            __result = utils.convertBytesToBase64(tab_bytes)
        print(f'stored data = {__result}')
        return __result


    @staticmethod
    def encryptData(value:str, tab:str):
        rs = generateKey.encode_str(value,tab)
        print(f'test decode = {generateKey.decode_str(rs)}')

        

        



# print(os.urandom(32))
# try:
#     with encoder() as en:
#         # Step 1
#         # en.generate_master_key
#         # step 2
#         # en.init_master_key
#         # step 3
#         # en.generate_encrytion_key
#         # en.init_key
#         # en.test_gen_key
#         # print(os.urandom(32))
#         #  encrypt data
#         # en.encrptionData('tan','tantan')
#         # test
#         # print(en.encrypt('test', os.urandom(16)))
#         # plaintext = "Chào mừng bạn đến với thế giới lập trình!"
#         # bytes_data = plaintext.encode('utf-8')
#         # print(bytes_data)
#         # print(type(bytes_data))
#         print(en.decrytData('tan'))

# except Exception as e:
#     print(e)