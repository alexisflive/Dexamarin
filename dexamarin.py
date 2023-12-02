import argparse
import os
import shutil
import struct
import lz4.block

header_xalz_magic = b"XALZ"
error_files = []


def decompile_assemblies(apk_path, out_dir_name):
    assemblies_folder_path = os.path.join(out_dir_name, "assemblies")
    shutil.unpack_archive(apk_path, out_dir_name, format="zip")

    for file_name in os.listdir(out_dir_name):
        if file_name != "assemblies":
            full_file_path = os.path.join(out_dir_name, file_name)
            try:
                if os.path.isdir(full_file_path):
                    shutil.rmtree(full_file_path)
                elif os.path.isfile(full_file_path):
                    os.remove(full_file_path)
                # else it is a special file socket, FIFO, device file (don"t do anything)
            except PermissionError:
                shutil.rmtree(full_file_path)

    # Use pyxamstore to unpack if the assemblies are inside an assemblies.blob file
    assemblies_blob = os.path.join(assemblies_folder_path, "assemblies.blob")
    if os.path.isfile(assemblies_blob):
        current_directory = os.getcwd()

        os.chdir(assemblies_folder_path)
        os.system("pyxamstore unpack")
        os.chdir(current_directory)

        output_folder = os.path.join(assemblies_folder_path, "out")
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                src_path = os.path.join(output_folder, file)
                dst_path = os.path.join(assemblies_folder_path, file)

                if os.path.exists(src_path):
                    shutil.move(src_path, dst_path)

        shutil.rmtree(output_folder)
        os.remove(assemblies_blob)
        os.remove(os.path.join(assemblies_folder_path, "assemblies.json"))
        os.remove(os.path.join(assemblies_folder_path, "assemblies.manifest"))

    # Decompress xalz compressed files
    for root, dirs, files in os.walk(assemblies_folder_path):
        for file in files:
            if file.endswith(".dll"):
                decompress_xalz(os.path.join(root, file))

    # Decompile .dll assemblies
    # (needs to occur in a separate loop because otherwise ilspycmd has issues opening the files)
    for root, dirs, files in os.walk(assemblies_folder_path):
        for file in files:
            if file.endswith(".dll"):
                decompile_assembly(os.path.join(root, file), out_dir_name)

    if not os.listdir(assemblies_folder_path):
        shutil.rmtree(assemblies_folder_path)

    if error_files:
        print("Dexamarin: error decompiling the following files: ")
        for errorFile in error_files:
            print("Dexamarin: error decompiling: " + errorFile)

    print(f"Dexamarin: finished decompiling the {apk_path} Xamarin assemblies")


def decompress_xalz(file_path, out_file_path=None):
    with open(file_path, "rb") as input_file:
        data = input_file.read()
        if out_file_path is not None:
            decompiled_file_path = out_file_path
        else:
            decompiled_file_path = input_file.name

        if data[:4] == header_xalz_magic:
            header_uncompressed_length = struct.unpack("<I", data[8:12])[0]
            payload = data[12:]

            decompressed = lz4.block.decompress(payload, uncompressed_size=header_uncompressed_length)

            with open(decompiled_file_path, "wb") as output_file:
                output_file.write(decompressed)

            print(f"Dexamarin: {output_file} was xalz decompressed")
            return decompiled_file_path

    return file_path


def decompile_assembly(assembly, out_dir_name=None):
    with open(assembly, "rb") as output_file:
        decompiled_file_path = output_file.name.replace(".dll", ".cs")

        if os.system(f"ilspycmd {output_file.name} > {decompiled_file_path} 2>/dev/null"):
            print(f"Dexamarin: there was an error decompiling {output_file.name}")
            error_files.append(output_file.name)
            os.remove(decompiled_file_path)
        else:
            os.remove(output_file.name)
            if out_dir_name is not None:
                shutil.move(decompiled_file_path, out_dir_name)

            print(f"Dexamarin: {output_file.name} was successfully decompiled")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decompile Xamarin apps")
    parser.add_argument("file", type=str,
                        help="the apk to decompile (or single assembly if the -s option is used)")
    parser.add_argument("-s", "--single-assembly", action="store_true",
                        help="decompile a single assembly rather than an apk")
    args = parser.parse_args()

    src_file = args.file
    if not args.single_assembly:
        out_name = src_file.replace(".apk", ".decompiled.assemblies")
        os.mkdir(out_name)
        decompile_assemblies(src_file, out_name)
    else:
        decompressed_name = decompress_xalz(src_file, src_file.replace(".dll", ".decompressed.dll"))
        decompile_assembly(decompressed_name, decompressed_name.replace(".decompressed.dll", ".decompiled.cs"))
