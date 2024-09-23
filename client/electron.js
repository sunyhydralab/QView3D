import { app, BrowserWindow, globalShortcut } from 'electron'
import electronSquirrelStartup from 'electron-squirrel-startup'
import path from 'path'

if (electronSquirrelStartup) app.quit()

const __dirname = app.getAppPath()

const createWindow = () => {

    const win = new BrowserWindow({
        width: 800,
        height: 600,
        icon: path.join(__dirname, './public/favicon2.ico'),
        show: false,
        noFrame: true,
        webPreferences: {
            preload: path.join(__dirname, './preload.js')
        }
    })
    win.maximize()
    win.loadFile(path.join(__dirname, './dist/index.html'))
    win.show()

    globalShortcut.register('Ctrl+Shift+C', () => {
        win.webContents.openDevTools()
    })
}

app.whenReady().then(() => {
    createWindow()
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})


app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})