import React, { Component } from "react";
import Base from "./Layouts/Base";

class App extends Component {
    page = "overview";
    render() {
        return (
            <div>
                <Base />
            </div>
        );
    }
}

export default App;
