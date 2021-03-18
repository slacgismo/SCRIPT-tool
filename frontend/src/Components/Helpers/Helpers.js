// Helper functions
import axios from "axios";
import { orderBy } from "lodash";

export function processResults(resultArr, isCBA) {
    const dataToVisualizeAll = [];
    let isTimeSeries = false;
    if (!resultArr) {
        resultArr = [];
    } else if (resultArr[0][Object.keys(resultArr[0])[0]][0].time) {
        isTimeSeries = true;
    }
    for (const result of resultArr) {
        const dataToVisualize = {};
        for (const field of Object.keys(result)) {
            let data = result[field];
            if (!isTimeSeries) {
                data = orderBy(data, ["year"], ["asc"]);
            }
            const dataFormatted = data.map((datapoint, i) => ({
                x: isTimeSeries ? i : datapoint.year,
                y: isTimeSeries
                    ? parseFloat(datapoint.load)
                    : parseFloat(datapoint.data),
            }));
            dataToVisualize[field] = {
                legendLabel: isCBA ? " " : `${field}`.replace(/_/g, " "),
                unit: isCBA ? `${field}`.replace(/_/g, " ") : "Power (kW)",
                xAxis: isTimeSeries ? "Time" : "Year",
                data: dataFormatted,
            };
        }
        dataToVisualizeAll.push(dataToVisualize);
    }
    return dataToVisualizeAll;
}

export function preprocessData(allData) {
    const data = allData.dataValues;
    const fields = data[0] ? Object.keys(data[0].values) : [0];
    const result = {};
    for (const field of fields) {
        result[field] = [];
    }
    data.forEach((dataItem) => {
        const year = dataItem.config.year;
        const allFields = dataItem.values;
        for (const field of fields) {
            result[field].push({
                year: year,
                data: parseFloat(allFields[field]),
            });
        }
    });
    const resultFlattened = [];
    for (const field of fields) {
        resultFlattened.push({
            [field]: result[field],
        });
    }
    return resultFlattened;
}

export async function checkFlowerTaskStatus(taskId) {
    const taskRes = await axios({
        url: `http://localhost:5555/api/task/result/${taskId}`,
        method: "get",
    });
    return taskRes.data.state;
}

export async function revokeCeleryTask(taskId) {
    await axios({
        url: `http://localhost:5555/api/task/revoke/${taskId}?terminate=true`,
        method: "post",
    });
}

export async function exponentialBackoff(
    checkStatus,
    taskId,
    timeout,
    max,
    delay,
    successCallback,
    failureCallback
) {
    let status = await checkStatus(taskId);
    if (status === "SUCCESS") {
        successCallback();
    } else if (status === "FAILURE") {
        failureCallback();
    } else if (max === 0) {
        revokeCeleryTask(taskId);
        failureCallback();
    } else if (status === "PENDING") {
        clearTimeout(timeout);
        timeout = setTimeout(function () {
            return exponentialBackoff(
                checkStatus,
                taskId,
                timeout,
                --max,
                delay * 2,
                successCallback,
                failureCallback
            );
        }, delay);
    }
}
