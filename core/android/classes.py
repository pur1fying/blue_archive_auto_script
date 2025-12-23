"""This module contains all Java classes used in the Android implementation.

.. NOTE::
    MUST be imported as soon as possible once Python **main thread** starts.

"""
from jnius import autoclass


Log = autoclass('android.util.Log')
String = autoclass('java.lang.String')
Toast = autoclass('android.widget.Toast')
ByteBuffer = autoclass('java.nio.ByteBuffer')
Bitmap = autoclass('android.graphics.Bitmap')
ComponentName = autoclass('android.content.ComponentName')
BitmapConfig = autoclass('android.graphics.Bitmap$Config')
PackageManager = autoclass('android.content.pm.PackageManager')

OcrEngine = autoclass('com.benjaminwan.ocrlibrary.OcrEngine')

Shizuku = autoclass('rikka.shizuku.Shizuku')
Shizuku_UserServiceArgs = autoclass('rikka.shizuku.Shizuku$UserServiceArgs')
ShizukuBinderWrapper = autoclass('rikka.shizuku.ShizukuBinderWrapper')
SystemServiceHelper = autoclass('rikka.shizuku.SystemServiceHelper')
ListenerInterfaceClass = autoclass('rikka.shizuku.Shizuku$OnRequestPermissionResultListener')
JavaArray = autoclass('java.lang.reflect.Array')

MainActivity = autoclass('org.baas.boa.MainActivity')
IUserService = autoclass('org.baas.boa.IUserService')
IUserService_Stub = autoclass('org.baas.boa.IUserService$Stub')
UserService = autoclass('org.baas.boa.UserService')
Java_CommandResult = autoclass('org.baas.boa.CommandResult')
Java_FsReadResult = autoclass('org.baas.boa.FsReadResult')
Java_FsStat = autoclass('org.baas.boa.FsStat')