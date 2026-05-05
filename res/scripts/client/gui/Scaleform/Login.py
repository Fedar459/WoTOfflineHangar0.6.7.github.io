import BigWorld
import ResMgr
import Settings
import MusicController
from ConnectionManager import _getClientUpdateUrl, connectionManager
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_DEBUG, LOG_WARNING
from helpers import i18n
from helpers.time_utils import makeLocalServerTime
from gui.Scaleform.Disconnect import Disconnect
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.windows import UIInterface
import Offline.Manager
Offline.Manager.init_offline()

class Login(UIInterface):
    _Login__APPLICATION_CLOSE_DELAY_DEFAULT = 15
    
    def __init__(self):
        self._Login__user = ''
        self._Login__host = ''
        self._Login__password = ''
        self._Login__predefinedServers = { }
        self._Login__publicKeys = { }
        self._Login__closeCallbackId = None
        UIInterface.__init__(self)

    
    def populateUI(self, proxy):
        UIInterface.populateUI(self, proxy)
        self.uiHolder.movie.backgroundAlpha = 1
        self.uiHolder.addExternalCallback('login.Login', self.onLogin)
        self.uiHolder.addExternalCallback('login.Register', self.onRegister)
        self._Login__loadUserConfig()
        self._Login__loadPredefinedServers(Settings.g_instance.scriptConfig['login'])
        connectionManager.connectionStatusCallbacks += self._Login__handleConnectionStatus
        connectionManager.onConnected += self._Login__onConnected
        connectionManager.searchServersCallbacks += self._Login__serversFind
        connectionManager.startSearchServers()
        connectionManager.onDisconnected -= Disconnect.show
        Disconnect.hide()
        self.setOptions(self._Login__predefinedServers.items())
        self._Login__loadVersion()
        Waiting.close()
        MusicController.g_musicController.stopAmbient()
        try:
            MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOGIN)
        except AttributeError:
            pass

    
    def dispossessUI(self):
        connectionManager.connectionStatusCallbacks -= self._Login__handleConnectionStatus
        connectionManager.onConnected -= self._Login__onConnected
        connectionManager.stopSearchServers()
        connectionManager.searchServersCallbacks -= self._Login__serversFind
        connectionManager.onDisconnected += Disconnect.show
        self.uiHolder.removeExternalCallback('login.Login')
        self.uiHolder.removeExternalCallback('login.Register')
        UIInterface.dispossessUI(self)

    
    def _Login__loadVersion(self):
        sec = ResMgr.openSection('../version.xml')
        version = sec.readString('appname') + ' ' + sec.readString('version')
        self.call('Login.SetVersion', [
            version])

    
    def _Login__loadUserConfig(self):
        ds = Settings.g_instance.userPrefs[Settings.KEY_LOGIN_INFO]
        if ds:
            self._Login__user = ds.readString('user')
            self._Login__host = ds.readString('host')
            self._Login__password = ds.readString('password')
            self.call('login.setDefaultValues', [
                self._Login__user,
                self._Login__password])
        

    
    def _Login__saveUserConfig(self):
        up = Settings.g_instance.userPrefs
        if up.has_key(Settings.KEY_LOGIN_INFO):
            li = up[Settings.KEY_LOGIN_INFO]
        else:
            li = up.write(Settings.KEY_LOGIN_INFO, '')
        li.writeString('user', self._Login__user)
        li.writeString('host', self._Login__host)
        if self._Login__password:
            li.writeString('password', self._Login__password)
        
        Settings.g_instance.save()

    
    def _Login__loadPredefinedServers(self, dataSection):
        if dataSection:
            for (name, host) in dataSection.items():
                name = None
                code = None
                key_path = None
                if host.has_key('name'):
                    name = host.readString('name')
                
                if host.has_key('url'):
                    code = host.readString('url')
                
                if host.has_key('public_key_path'):
                    key_path = host.readString('public_key_path')
                
                if code is not None:
                    if name is not None:
                        self._Login__predefinedServers[code] = name
                    
                    if key_path is not None:
                        self._Login__publicKeys[code] = key_path
                    
                key_path is not None
            
        

    
    def _Login__serversFind(self, servers = None):
        list = self._Login__predefinedServers.items()
        if servers is not None:
            for (name, key) in servers:
                if key not in self._Login__predefinedServers.keys():
                    list.append((key, name))
                    continue
            
        
        self.setOptions(list)


    
    def _Login__handleConnectionStatus(self, stage, status, serverMsg):
        if stage == 1:
            if status != 'LOGGED_ON':
                errorMessage = i18n.makeString('#menu:login/status/' + status)
                if status == 'LOGIN_CUSTOM_DEFINED_ERROR':
                    (expiryTime, reason) = serverMsg.split(';', 2)
                    reason = i18n.makeString(reason)
                    expiryTime = int(expiryTime)
                    if expiryTime != 0:
                        expiryTime = makeLocalServerTime(int(expiryTime))
                        expiryTime = BigWorld.wg_getLongDateFormat(expiryTime) + ' ' + BigWorld.wg_getLongTimeFormat(expiryTime)
                        errorMessage %= {
                            'time': expiryTime,
                            'reason': reason }
                    else:
                        errorMessage = i18n.makeString('#menu:login/status/LOGIN_CUSTOM_DEFINED_ERROR2')
                        errorMessage %= {
                            'reason': reason }
                
                self._Login__setStatus(errorMessage)
                if connectionManager.isUpdateClientSoftwareNeeded():
                    self._Login__handleUpdateClientSoftwareNeeded()
                else:
                    connectionManager.disconnect()
            
        elif stage == 6:
            self._Login__setStatus(i18n.convert(i18n.makeString('#menu:login/status/disconnected')))
            connectionManager.disconnect()
        

    
    def _Login__onConnected(self):
        LOG_DEBUG('onConnected')

    
    def _Login__handleUpdateClientSoftwareNeeded(self):
        updateUrl = _getClientUpdateUrl()
        text = i18n.convert(i18n.makeString('#menu:login/updateURLAvaialbleAt')) % updateUrl
        self._Login__setStatus(text)
        LOG_WARNING('Client software update needed. Update URL: %s' % updateUrl)
        if True:
            self._Login__closeCallbackId = BigWorld.callback(self._Login__getApplicationCloseDelay(), BigWorld.quit)
            
            try:
                import webbrowser as webbrowser
                webbrowser.open_new(updateUrl)
            except Exception:
                LOG_CURRENT_EXCEPTION()
            


    
    def _Login__getApplicationCloseDelay(self):
        prefs = Settings.g_instance.userPrefs
        if prefs is None:
            delay = Login._Login__APPLICATION_CLOSE_DELAY_DEFAULT
        elif not prefs.has_key(Settings.APPLICATION_CLOSE_DELAY):
            prefs.writeInt(Settings.APPLICATION_CLOSE_DELAY, Login._Login__APPLICATION_CLOSE_DELAY_DEFAULT)
        
        delay = prefs.readInt(Settings.APPLICATION_CLOSE_DELAY)
        return delay

    
    def setOptions(self, optionsList):

        options = [0]
        options.append('offline server')
        options.append('localhost:2001')

        for key, name in optionsList:
            options.append(name)
            options.append(key)
     
        self.call('login.setServersList', options)

    
    def _Login__setStatus(self, status):
        self.call('login.setErrorMessage', [
            status])
        Waiting.close()

    
    def onLogin(self, id, user, password, host):
        if self._Login__closeCallbackId:
            BigWorld.cancelCallback(self._Login__closeCallbackId)
            self._Login__closeCallbackId = None
        
        self._Login__user = user.lower().strip()
        if len(self._Login__user) > 1:
            Waiting.show('#menu:waiting/login')
            self._Login__password = password.strip()
            self._Login__host = host
            self._Login__saveUserConfig()
            publicKey = self._Login__publicKeys.get(host, None)
            connectionManager.connect(self._Login__host, self._Login__user, self._Login__password, publicKey)
        else:
            self._Login__setStatus(i18n.convert(i18n.makeString('#menu:login/status/invalid_login')))

    
    def onRegister(self, callbackID):
        openRegistrationWebsite = openRegistrationWebsite
        import game
        openRegistrationWebsite()


