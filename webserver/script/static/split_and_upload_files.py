import argparse
import boto3


SESSION_LENGTH = 590000
INTERVAL_LENGTH = 2500000


def get_parameters():
    parser = argparse.ArgumentParser(description='Split files and upload them to S3 bucket.')
    parser.add_argument('bucket_name', help='bucket name')
    parser.add_argument('data_type', help='data type: residential or commercial')
    parser.add_argument('file_type', help='file type: internal or session')
    parser.add_argument('file_name', help='file name')

    args = parser.parse_args()
    bucket_name = args.bucket_name
    data_type = args.data_type
    file_type = args.file_type
    filename = args.file_name

    return bucket_name, data_type, file_type, filename


def split_file(file_type, filename):

    if file_type == "session":
        length = SESSION_LENGTH
    else:
        length = INTERVAL_LENGTH

    csv_file = open(filename, 'r').readlines()
    suffix = 0
    header = csv_file[0]
    file_list = []

    for i in range(len(csv_file)):
        if i % length == 0:

            if suffix != 0:
                open(str(suffix) + '_' + filename, 'a+').writelines(header)
                open(str(suffix) + '_' + filename, 'a+').writelines(csv_file[i: i + length])

            if suffix == 0:
                open(str(suffix) + '_' + filename, 'a+').writelines(csv_file[i: i + length])

            if str(suffix) + '_' + filename not in file_list:
                file_list.append(str(suffix) + '_' + filename)

            suffix += 1

    return file_list


def upload_s3(bucket, local_file, destination_file):
    s3 = boto3.client('s3')
    s3.upload_file(local_file, bucket, destination_file)


def upload_files(file_list, bucket, path):
    print("There are the total of " + str(len(file_list)) + " files to upload.")

    for file in file_list:
        print("Uploading " + file + " ...")
        upload_s3(bucket, file, path + file)


def split_upload():
    print("Start...")
    bucket_name, data_type, file_type, filename = get_parameters()
    print("Splitting files...")
    file_list = split_file(file_type, filename)
    upload_files(file_list, bucket_name, file_type + "/" + data_type + "/")
    print("Done!")


split_upload()