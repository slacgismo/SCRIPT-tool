import React, { Component } from "react";
import Base from "../../Layouts/Base";
import OverviewMap from "../OverviewMap/OverviewMap";

class Overview extends Component {
    render() {
        return (
            <div>
                <Base content={<OverviewMap />} />
            </div>
        );
    }
}

export default Overview;
