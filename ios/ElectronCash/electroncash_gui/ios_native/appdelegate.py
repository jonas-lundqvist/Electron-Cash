#!/usr/bin/env python3
#

from .uikit_bindings import *
from . import gui
from . import heartbeat
from . import utils
import ElectronCash.app

class PythonAppDelegate(UIResponder):
    
    @objc_method
    def application_willFinishLaunchingWithOptions_(self, application : ObjCInstance, launchOptions : ObjCInstance) -> bool:
        # tell iOS that our app refreshes content in the background
        #application.setMinimumBackgroundFetchInterval_(UIApplicationBackgroundFetchIntervalMinimum)
        #bgStatus = "Enabled for this app." if UIBackgroundRefreshStatusAvailable == int(application.backgroundRefreshStatus) else "DISABLED"
        #print("Background refresh status: %s\nBackground fetch minimum interval: %f s\nMinimum Keep Alive Timeout: %f s"%(bgStatus,UIApplicationBackgroundFetchIntervalMinimum,UIMinimumKeepAliveTimeout))
        return True

    @objc_method
    def application_didFinishLaunchingWithOptions_(self, application : ObjCInstance, launchOptions : ObjCInstance) -> bool:
        print("App finished launching.")

        ElectronCash.app.main()

        return True

    # NB: According to apple docs, it's bad to abuse this method if you actually do no downloading, so disabled.
    # If we reenable be sure to add the appropriate BackgroundModes key to Info.plist
    '''@objc_method
    def application_performFetchWithCompletionHandler_(self, application : ObjCInstance, completionHandler : ObjCInstance) -> None:
        print("Background: WOAH DUDE! AppDelegate fetch handler called! It worked!")
        print("Background: About to call completion handler.. lord have mercy!")
        ObjCBlock(completionHandler)(UIBackgroundFetchResultNewData)
    '''
    
    @objc_method
    def application_didChangeStatusBarOrientation_(self, application, oldStatusBarOrientation: int) -> None:
        print("ROTATED", oldStatusBarOrientation)
        gui.ElectrumGui.gui.on_rotated()

## BG/FG management... do some work in the BG

    @objc_method
    def applicationDidBecomeActive_(self, application : ObjCInstance) -> None:
        msg = "App became active " + cleanup_possible_bg_task_stuff()
        utils.NSLog("%s",msg)
        
        eg = gui.ElectrumGui.gui
        if eg is not None and not eg.daemon_is_running():
            utils.NSLog("Background: Restarting Daemon...")
            eg.start_daemon()
        

    @objc_method
    def applicationDidEnterBackground_(self, application : ObjCInstance) -> None:
        startup_bg_task_stuff(application)


## Global helper functions for this bgtask stuff
bgTask = UIBackgroundTaskInvalid
bgTimer = None

def startup_bg_task_stuff(application : ObjCInstance) -> None:
    global bgTask
    global bgTimer
    utils.NSLog("Background: Entered background, notifying iOS about bgTask, starting bgTimer.")#, starting up heartbeat.")

    bgTask = application.beginBackgroundTaskWithName_expirationHandler_(at("Electron_Cash_Background_Task"), on_bg_task_expiration)        

    wasRunning = heartbeat.IsRunning()
    #heartbeat.Start() # not sure if this makes much of a difference yet.. so don't use
    if wasRunning: utils.NSLog("Background: Heartbeat was already active in foreground. FIXME!")
    if bgTimer is not None: utils.NSLog("Background: bgTimer was not None. FIXME!")
    
    def onTimer() -> None:
        global bgTask
        global bgTimer
        bgTimer = None
        if bgTask != UIBackgroundTaskInvalid:
            utils.NSLog("Background: Our expiry timer fired, will force expiration handler to execute early.")
            on_bg_task_expiration()
        else:
            utils.NSLog("Background: Our expiry timer fired, but bgTask was already stopped.")
    
    utils.NSLog("Background: Time remaining is %f secs.",float(application.backgroundTimeRemaining))
    bgTimer = utils.call_later(min(178.0,max(application.backgroundTimeRemaining-2.0,0.0)),onTimer) # if we don't do this we get problems because iOS freezes our task and that crashes stuff in the daemon

def cleanup_possible_bg_task_stuff() -> str:
    global bgTask
    global bgTimer

    msg = ""
    
    if bgTimer is not None:
        bgTimer.invalidate()
        bgTimer = None
        msg += "killed extant bgTimer"
    else:
        msg += "no bgTimer was running"
        
    if heartbeat.IsRunning():
        heartbeat.Stop()
        msg += ", sent stop to heartbeat"
    else:
        msg += ", heartbeat was not running"
    if bgTask != UIBackgroundTaskInvalid:
        UIApplication.sharedApplication.endBackgroundTask_(bgTask)
        bgTask = UIBackgroundTaskInvalid
        msg += ", told UIKit to end our bgTask"
    else:
        msg += ", we did not have a bgTask active"
    return msg
    
def on_bg_task_expiration() -> None:
    utils.NSLog("Background: Expiration handler called")
    
    daemonStopped = False
    eg = gui.ElectrumGui.gui
    if eg is not None and eg.daemon_is_running():
        utils.NSLog("Background: Stopping Daemon...")
        eg.stop_daemon()
        daemonStopped = True

    msg = "Background: "
    msg += cleanup_possible_bg_task_stuff()
    msg += ", stopped daemon" if daemonStopped else ""
    utils.NSLog("%s",msg)
    
