import arcpy, os

def ScriptTool(workspace):
    # Script execution code goes here
    return

# This is used to execute code if the file was run but not imported
if __name__ == '__main__':
    
    # Get the current project
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Get the default geodatabase of the project
    default_workspace = os.path.join(aprx.filePath, "woodpeckerNC.gdb")

    # Create a parameter object for the workspace parameter
    workspace_param = arcpy.Parameter(
        displayName="Workspace",
        name="workspace",
        datatype="Workspace",
        parameterType="Required",
        direction="Input"
    )

    # Set the default value of the workspace parameter
    workspace_param.value = default_workspace

    # Create a parameter list and add the workspace parameter
    params = [workspace_param]

    # Call the script tool function with the parameter list
    ScriptTool(*params)
