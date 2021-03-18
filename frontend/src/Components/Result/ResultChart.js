import React from "react";
import "../../../node_modules/react-vis/dist/style.css";
import {
    XYPlot,
    LineSeries,
    HorizontalGridLines,
    XAxis,
    YAxis,
    ChartLabel,
    DiscreteColorLegend,
} from "react-vis";
import "./ResultChart.css";

class ResultChart extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        const colors = [
            "#e62020",
            "#e3b920",
            "#63b81a",
            "#25c3db",
            "#3b22e0",
            "#c921db",
            "#911955",

            "#e62020",
            "#e3b920",
            "#63b81a",
            "#25c3db",
            "#3b22e0",
            "#c921db",
            "#911955",

            "#e62020",
            "#e3b920",
            "#63b81a",
            "#25c3db",
            "#3b22e0",
            "#c921db",
            "#911955",
        ];
        const { results } = this.props;
        const newItems = [];
        const newData = [];
        Object.keys(results).forEach((attr, i) => {
            newItems.push({
                title: results[attr].legendLabel,
                color: colors[i],
            });
            newData.push({
                key: attr,
                data: results[attr].data,
                color: colors[i],
            });
        });

        return (
            <div className="chart-grid">
                {
                    /* title of chart */
                    <h5 className="chartTitle">{this.props.chartTitle}</h5>
                }
                <XYPlot
                    margin={{ top: 20, right: 60 }}
                    height={this.props.graphHeight}
                    width={this.props.graphWidth}
                >
                    {this.props.legendPosition === "right" &&
                        !this.props.isCBA && (
                            <DiscreteColorLegend
                                style={{
                                    position: "absolute",
                                    left: this.props.graphWidth + 40,
                                    top: "15px",
                                    width: "13rem",
                                }}
                                orientation="vertical"
                                items={newItems}
                            />
                        )}

                    <HorizontalGridLines />
                    {newData.map((newDataPiece) => (
                        <LineSeries
                            key={newDataPiece.key}
                            data={newDataPiece.data}
                            color={newDataPiece.color}
                        />
                    ))}
                    <XAxis
                        position="end"
                        tickFormat={(d) => {
                            if (
                                this.props.results[
                                    Object.keys(this.props.results)[0]
                                ].xAxis === "Time"
                            ) {
                                const HOUR_INCREMENT = 15;
                                let minute = !(d % 100)
                                    ? d
                                    : d * HOUR_INCREMENT;
                                return `${Math.floor(minute / 60)
                                    .toString()
                                    .padStart(2, "0")}:${(minute % 60)
                                    .toString()
                                    .padStart(2, "0")}`;
                            } else {
                                return d;
                            }
                        }}
                    />
                    {this.props.legendPosition !== "none" && (
                        <ChartLabel
                            text={
                                this.props.results[
                                    Object.keys(this.props.results)[0]
                                ].xAxis
                            }
                            className="alt-x-axis"
                            includeMargin={false}
                            xPercent={1.03}
                            yPercent={1.23}
                            style={{
                                textAnchor: "end",
                                fontWeight: "bold",
                            }}
                        />
                    )}
                    {this.props.legendPosition !== "none" && (
                        <ChartLabel
                            text={
                                this.props.results[
                                    Object.keys(this.props.results)[0]
                                ].unit
                            }
                            className="alt-y-label"
                            includeMargin={false}
                            xPercent={0.0}
                            yPercent={0.035}
                            style={{
                                fontWeight: "bold",
                            }}
                        />
                    )}
                    <YAxis
                        position="end"
                        tickLabelAngle={-20}
                        tickTotal={9}
                        tickFormat={(d) => {
                            if (d >= Math.pow(10, 15)) {
                                return `${d / Math.pow(10, 15)}P`;
                            } else if (d >= Math.pow(10, 12)) {
                                return `${d / Math.pow(10, 12)}T`;
                            } else if (d >= Math.pow(10, 9)) {
                                return `${d / Math.pow(10, 9)}G`;
                            } else if (d >= Math.pow(10, 6)) {
                                return `${d / Math.pow(10, 6)}M`;
                            } else if (d >= Math.pow(10, 3)) {
                                return `${d / Math.pow(10, 3)}K`;
                            } else {
                                return d;
                            }
                        }}
                    />
                </XYPlot>
            </div>
        );
    }
}

export default ResultChart;
