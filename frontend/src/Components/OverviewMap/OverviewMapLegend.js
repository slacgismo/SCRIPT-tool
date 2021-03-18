import React from "react";
import { ContinuousColorLegend } from "react-vis";

function OverviewMapLegend(props) {
    return (
        <ContinuousColorLegend
            style={{
                margin: "3rem",
            }}
            startTitle={`${props.startValue} ${props.unit}`}
            midTitle={`${props.midValue} ${props.unit}`}
            endTitle={`${props.endValue} ${props.unit}`}
            startColor={props.startColor}
            endColor={props.endColor}
            width={250}
        />
    );
}

export default OverviewMapLegend;
