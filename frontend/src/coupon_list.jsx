import $ from 'jquery'
import Time from 'react-time';
import React from "react";
import ReactDOM from "react-dom";

import {Table} from 'react-bootstrap';
import {Input} from 'react-bootstrap';

const API_URL = '/api/1/'

class CouponListUI extends React.Component {
    constructor(props) {
        super(props);
        let now = new Date();
        this.state = {
            data: {
                coupons: []
            },
            filter: {
                year: now.getFullYear()
            }
        }
    }

    componentDidMount() {
        this.fetchData()
    }

    fetchData() {
        $.ajax({
            url: API_URL + "coupons",
            data: this.state.filter,
            method: 'GET',
            dataType: 'json',
        }).done((resp) => {
            this.setState({data: resp})
        })
    }

    refresh() {
        this.setState({filter: this.state.filter})
        this.fetchData()
    }
    renderFilterForm() {
        let filter = this.state.filter

        return (
            <div>
            <form className="form-inline">
                <Input type='select'
                    label="Metai&nbsp;"
                    value={this.state.filter.year}
                    onChange={(evt) => {filter.year = evt.target.value; this.refresh()}}>
                    <option value="2016">2016</option>
                    <option value="2015">2015</option>
                    <option value="2014">2014</option>
                    <option value="2013">2013</option>
                    <option value="2012">2012</option>
                </Input>
            </form>
            </div>
        )
    }

    renderCouponRow(coupon, n) {
        function formatCouponType(me, ctype) {
            return me.state.data.refs.coupon_types[ctype];
        }

        let urlpat = decodeURIComponent(this.state.data.refs.coupon_url_pattern);
        function formatCouponUrl(me, coupon_id) {
            return urlpat.replace('@@@', coupon_id)
        }

        return (
            <tr key={coupon.__key}>
                <td><a href={ formatCouponUrl(this, coupon.__name) }>{ coupon.__name }</a></td>
                <td><a href="mailto:{ coupon.order.payer_email }">{coupon.order.payer_email}</a></td>
                <td>{formatCouponType(this, coupon.order.coupon_type)}</td>
                <td><Time value={coupon.order.payment_time} format="YYYY-MM-DD" /></td>
                <td>{coupon.order.paid_amount} { coupon.order.paid_currency}</td>
                <td>{coupon.order.notes}</td>
                <td>{coupon.order.test}</td>
            </tr>
        )
    }

    render() {
        return (
            <div>
            <h1>Galiojantys kvietimai</h1>
            <div className="pull-right">
                {this.renderFilterForm()}
            </div>
            <p>Galiojančių kvietimų: {this.state.data.count}</p>
            <Table condensed bordered hover >
                <thead>
                  <tr>
                    <th>Nr</th>
                    <th>Email</th>
                    <th>Tipas</th>
                    <th>Pirkimo data</th>
                    <th>Sumokėta</th>
                    <th>Pastabos</th>
                    <th>Testinis?</th>
                  </tr>
                </thead>
                <tbody>
                    {this.state.data.coupons.map((coupon) => {return this.renderCouponRow(coupon)})}
                </tbody>
            </Table>

            </div>
        )
    }
}

export function renderCouponList(elem) {
    // test
    ReactDOM.render(
      <CouponListUI name="World"/>,
      elem
    );
}
