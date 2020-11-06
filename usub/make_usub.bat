@echo OFF
if exist standardU.dll del standardU.dll
if exist usub_3d-std.obj del usub_3d-std.obj

abaqus make library=usub_3d.for
