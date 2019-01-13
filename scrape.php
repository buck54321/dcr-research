<?php

include("../strataminer/scripts/Sentinel.php");
$sentinel = new Sentinel;

$currencyInfo = json_decode(file_get_contents("../strataminer/api/currency-template.json"), true);

foreach($currencyInfo as $symbol => $info){

	$query = 'SELECT symbol_id FROM symbols WHERE symbol=?';
	$sentinel->prep_bind_execute($query, ["s", $symbol], "grab_symbol");
	$rows = $sentinel->get_array(["symbol.id"]);
	if(count($rows) == 0){
		$query = 'INSERT INTO symbols(symbol) VALUES(?)';
		if( ! $sentinel->prep_bind_execute($query, ["s", $symbol], "insert_symbol") ){
			echo("mysql error: ".$sentinel->errmsg."\n");
			continue;
		}		
		$symbolId = $sentinel->insert_id();
	}
	else{
		$symbolId = $rows[0]["symbol.id"];
	}
	$query = 'SELECT date_stamp FROM market_data WHERE symbol_id=? ORDER BY date_stamp DESC LIMIT 1';
	if( ! $sentinel->prep_bind_execute($query, ["i",$symbolId], "get_last_stamp") ){
		echo("mysql error: ".$sentinel->errmsg."\n");
		continue;
	}
	$rows = $sentinel->get_array(["stamp"]);	
	$lastStamp = 0;
	if(count($rows) == 0){
		$lastStampString = "20130428";
	}
	else{
		$lastStamp = $rows[0]["stamp"];
		$lastStampString = strftime("%Y%m%d", $lastStamp);
	}
	$todayString = strftime("%Y%m%d"); // Returns time right now
	echo(sprintf("fetching data for %s\n", $symbol));
	//https://coinmarketcap.com/currencies/denarius-dnr/historical-data/?start=%s&end=%s
	$uri = sprintf("https://coinmarketcap.com/currencies/%s/historical-data/?start=%s&end=%s", $info["cmc.token"], $lastStampString, $todayString);
	$html = file_get_contents($uri);
	if(empty($html)){
		continue;
	}
	$page = new DOMDocument;
	libxml_use_internal_errors(true);
	$page->loadHTML($html);
	libxml_use_internal_errors(false);
	$tableRows = $page->getElementById("historical-data")->getElementsByTagName("tbody")->item(0)->getElementsByTagName("tr");

	echo($tableRows->length." rows retrieved\n");

	$query = "INSERT INTO market_data(symbol_id, date_stamp, open_value, high, low, close_value, volume, market_cap) VALUES (?,?,?,?,?,?,?,?)";
	// $sentinel->prep($query, "prep_query");
	$params = array("sidddddd");
	$params[1] = $symbolId;// symbol
	foreach($tableRows as $tr){
		if($tr->getAttribute("class") != "text-right"){
			continue;
		}
		$tdNodes = $tr->getElementsByTagName("td");
		if($tdNodes->length != 7){
			continue;
		}
		// ["date.string","open","high","low","close","volume","market.cap"]
		$dtStr = $tdNodes->item(0)->nodeValue." 12";
		$dt = DateTime::createFromFormat("F d, Y G", $dtStr);
		$dateStamp = $dt->getTimestamp();
		if($dateStamp <= $lastStamp){
			continue;
		}
		$params[2] = $dateStamp;// date_stamp
		$params[3] = floatval(str_replace(",", "", $tdNodes->item(1)->nodeValue));// open_value
		$params[4] = floatval(str_replace(",", "", $tdNodes->item(2)->nodeValue));// high
		$params[5] = floatval(str_replace(",", "", $tdNodes->item(3)->nodeValue));// low
		$params[6] = floatval(str_replace(",", "", $tdNodes->item(4)->nodeValue));// close_value
		$params[7] = floatval(str_replace(",", "", $tdNodes->item(5)->nodeValue));// volume
		$params[8] = floatval(str_replace(",", "", $tdNodes->item(6)->nodeValue));// market_cap
		// $open = floatval($tdNodes->item(1)->nodeValue);
		// $high = floatval($tdNodes->item(2)->nodeValue);
		// $low = floatval($tdNodes->item(3)->nodeValue);
		// $close = floatval($tdNodes->item(4)->nodeValue);
		// $volume = floatval($tdNodes->item(5)->nodeValue);
		// $marketCap = floatval($tdNodes->item(6)->nodeValue);
		if( ! $sentinel->prep_bind_execute($query, $params, "insert_market_point") ){
			echo("mysql error: ".$sentinel->errmsg."\n");
		};
	}
	$sentinel->stmt->close();
	$sentinel->stmt = false;
	sleep(rand(2,10));
}

?>