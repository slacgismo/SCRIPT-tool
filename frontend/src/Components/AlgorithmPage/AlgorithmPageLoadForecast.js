import React from "react";
import AlgorithmPage from "./AlgorithmPage";
import AlgorithmInputsLoadForecast from "../AlgInputs/AlgInputsLoadForecast";

function AlgorithmPageLoadForecast(props) {
    return (
        <AlgorithmPage
            title={"Load Forecast"}
            graphWidth={600}
            algInputs={AlgorithmInputsLoadForecast}
        />
    );
}

export default AlgorithmPageLoadForecast;
