<img src="togglegroupvisibility.svg" width="80" height="80"/>
<img src="doc/ibama.svg" hspace="200"/>

# Toggle Group Visibility Plugin  

***Toggle Group Visibility*** is a panel plugin for change a visible item(group or layer) inside a group(mutually exclusive), that can be done manually or automatically, by buttons or shortcuts of keyboard.  
![alt-text-1](doc/panel.png "Panel")  

## Steps: ##  

* **Define a group for change the visibility of its items :**  
  * Add panel in QGIS.  
<img src="doc/add_panel_menu.png" width="300" height="400"/>
<img src="doc/add_panel_icon.png"/>
  * Select a group.  
  \* The select group is the current group  in layers panel.  
<img src="doc/select_group_panel.png" width="150" height="250"/>


* **Plugin Panel:**  
  * Up: Change visibility to the above item(shortcut '<').
  * Down: Change visibility to the below item(shortcut '>').
  * Loop: Change visibility automatically(shortcut 'L').
    * Time: The time in seconds to change item.
    * Direction: Up(above) or Down(below).
  * Set current: Set the visible item in layer panel(shortcut '?').
  * Copy: Copy the visible item to 'GroupVisibility' group(shortcut 'C').
  * Enable shortcuts: Enable/disable shortcuts

* **Example:**
![alt-text-1](doc/togglegroup.gif "Example")
