import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './CarList.css';
import { Link } from 'react-router-dom'

const CarList = () => {
  const [carData, setCarData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAllPrices, setShowAllPrices] = useState({});

  useEffect(() => {
    //axios.get('http://127.0.0.1:8080/api/olx_finn_data') //for dev testing
    axios.get('https://backend-server-hcvn.onrender.com/api/olx_finn_data_after2015') //above api hosted by third party
      .then(response => {
        setCarData(response.data);
        setLoading(false);
      })
      .catch(error => {
        setError(error);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>This should not take more than 50 seconds...</p>;
  if (error) return <p>Error loading data: {error.message}</p>;

  function TurnToBAM(parameter) {
    return (parameter / 5.85).toFixed(0)
  }
  const BaseOLXUrl = "https://olx.ba/artikal/";

  const toggleShowPrices = (id) => {
    setShowAllPrices(prev => ({ ...prev, [id]: !prev[id] }));
  }

  carData.sort((a, b) => b.olx_prices.length - a.olx_prices.length); //sorts cars with most olx matches first
  const filteredCars = carData.filter(car => car.car_name.toLowerCase().includes(searchTerm)); //for displaying number of results on page

  return (
    <div className="car-list">
      <div className="buttonbar">
      <div className="button">
        <Link to="/Home" style={{ textDecoration: 'none' }}>
            <button style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer',position: 'sticky' }}>
                Before 2015
            </button>
        </Link>
      </div>
      </div>
      <div className="search-bar-container">
        <input
          type="text"
          placeholder="Search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value.toLowerCase())}
          className="search-bar"
        />
        <div className="result-count">Results: {filteredCars.length}</div>

      </div>
      {carData.filter(car => car.car_name.toLowerCase().includes(searchTerm)).map((car, index) => (
        <div key={index} className="car-card">

          <h2>{car.car_name}</h2>
          <img src={car.image_url} alt={car.car_name} className="car-image" />

          <p><strong>Finn.no link:</strong> <a href={car.finn_link} target="_blank" rel="noopener noreferrer">{car.finn_link}</a></p>
          <p><strong>Finn.no price:</strong> {car.finn_price} NOK / {TurnToBAM(car.finn_price)} BAM </p>
          <p><strong>OLX.ba prices:</strong> {
            car.olx_prices
            .map((price, i) => ({ price, url: `${BaseOLXUrl}${car.olx_ids[i]}` }))
            .sort((a, b) => b.price - a.price)
            .slice(0, showAllPrices[car.car_name] ? car.olx_prices.length : 5)
            .map((item, i, arr) => (
              <span key={i}>
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="olx-link">
                  {item.price === 0 ? 'Na upit' : item.price}
                </a>
                {i < arr.length - 1 && ', '}
              </span>
            ))
          }
          {car.olx_prices.length > 5 && (
            <button onClick={() => toggleShowPrices(car.car_name)} className="more-button">
              {showAllPrices[car.car_name] ? 'Less' : 'Show more...'}
            </button>
          )}
          </p>
    
          <p><strong>Year:</strong> {car.year}</p>
          <p><strong>Norwegian tax return estimate:</strong> {car.tax_return} NOK / {TurnToBAM(car.tax_return)} BAM</p>
        </div>
      ))}
    </div>
  );
};

export default CarList;