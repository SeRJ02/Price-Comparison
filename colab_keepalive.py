# === COLAB CELL: Keep-Alive (Task 10.1) ===
# Run this cell to prevent Colab timeout (~90 min inactivity disconnect)

from IPython.display import display, Javascript

display(Javascript('''
function ClickConnect(){
    console.log("Keeping alive...");
    document.querySelector("colab-toolbar-button#connect").click()
}
setInterval(ClickConnect, 60000)
'''))
print("⏰ Keep-alive active — clicking connect every 60 seconds")
