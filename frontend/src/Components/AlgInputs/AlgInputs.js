import React from "react";
import { processResults } from "../Helpers/Helpers";

export default function AlgInputs(props) {
    const visualizeResults = (resultArr, isCBA) => {
        props.visualizeResults(processResults(resultArr, isCBA));
    };

    const AlgInputCustomized = props.algInputs;

    return (
        <div>
            <form noValidate autoComplete="off">
                <AlgInputCustomized
                    controlType={props.controlType}
                    visualizeResults={(result, isCBA) =>
                        visualizeResults(result, isCBA)
                    }
                    setChartTitles={(chartTitles) =>
                        props.setChartTitles(chartTitles)
                    }
                    checkCBA={(isCBA) => props.checkCBA(isCBA)}
                    loadingResults={(isLoading) =>
                        props.loadingResults(isLoading)
                    }
                />
            </form>
        </div>
    );
}
