import React from "react";
import Base from "../../Layouts/Base";
import Button from "@material-ui/core/Button";

class Download extends React.Component {
    constructor(props) {
        super(props);
    }

    downloadScript = () => {
        window.open("http://localhost:8000/static/split_and_upload_files.py");
    };

    render() {
        const instructions = (
            <div>
                <h2>Instructions</h2>
                When uploading, you need to provide parameters (see below
                Parameters part) indicating which path should the files be
                uploaded to. The script you download here is used to split large
                files into smaller ones and upload all these files into related
                S3 buckets under related paths
                <h3>Dependencies</h3>
                <li>Python3 installed.</li>
                <li>boto3 installed. </li>
                <h3>Parameters</h3>
                <li>
                    s3 bucket name: name of the S3 bucket you want to upload
                    files to{" "}
                </li>
                <li>data type: enter commercial or residential </li>
                <li>file type: enter session or interval </li>
                <li>
                    filename: name of the file you want to upload to S3 bucket{" "}
                </li>
                <h3>Command</h3>
                <dt>Enter the below command to upload files to S3 bucket</dt>
                <dd>
                    <code>
                        python3 split_and_upload_files.py &#123; S3 bucket name
                        &#125; &#123; data type &#125; &#123; file type &#125;
                        &#123; filename &#125;
                    </code>
                </dd>
                <dt>For example:</dt>
                <dd>
                    <code>
                        python3 split_and_upload_files.py script.test.raw
                        commercial session session_test.csv
                    </code>
                </dd>
                By running the above command, file session_test.csv will be
                uploaded to S3 bucket script.test.raw under this path
                session/commercial
                <h3>Note</h3>
                After splitting, the file filename.csv will be split into
                several files with name as 0_filename.csv, 1_filename.csv,
                2_filename.csv...
                <br />
                <br />
            </div>
        );

        return (
            <div>
                <Base
                    content={
                        <div>
                            <h2>Download Script</h2>
                            <Button
                                variant="outlined"
                                onClick={this.downloadScript}
                            >
                                Download Script
                            </Button>
                            <p />
                            {instructions}
                        </div>
                    }
                />
            </div>
        );
    }
}

export default Download;
