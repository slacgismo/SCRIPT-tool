import React, { Component } from "react";
import Base from "../../Layouts/Base";
import { DropzoneArea } from "material-ui-dropzone";

class Upload extends Component {
    constructor(props) {
        super(props);
        this.state = {
            files: [],
        };
    }
    handleChange(files) {
        this.setState({
            files: files,
        });
    }

    render() {
        return (
            <div>
                <Base
                    content={
                        <div>
                            <DropzoneArea
                                acceptedFiles={["text/plain"]}
                                dropzoneText="Drag and drop a file here or click"
                                showPreviews={true}
                                showPreviewsInDropzone={false}
                                filesLimit="1"
                                maxFileSize={5000000}
                                showFileNamesInPreview="true"
                                onChange={this.handleChange.bind(this)}
                            />
                        </div>
                    }
                />
            </div>
        );
    }
}

export default Upload;
