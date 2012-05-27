#!/usr/bin/perl -w
# RuterSearch Admin
#########################################################
#        RuterSearch Administration Program             #
#          by Weston Ruter (RuterSoft)                  #
#          Copyright 2000                               #
#          http://www.Ruter.net/                        #
#########################################################
# All code is copyrighted by Weston Ruter (RuterSoft).  #
# You may not redistribute or resell this program       #
# without expressed written consent.                    #
#########################################################

#startfile

use strict;
use DBI;

print "Content-type: text/html\n\n";

sub htmlhead;
sub htmldtd;
sub htmlfoot;
sub trim;
sub backButton;
sub errorMsg;
sub reportError;
sub readQuery;
sub httpQueryVars;
sub htmlEntities;
sub getConfig;
sub putConfig;
sub openDatabase;
sub getFields;
sub closeDatabase;
sub truechecked;
sub falsechecked;
sub relogin;
sub cgidie;

my %entryFields = ();
my $query = &readQuery;
my %query = &httpQueryVars('text', $query);
my %hexQuery = &httpQueryVars('urlencoded', $query);
my %htmlQuery = &httpQueryVars('html', $query);
my %config = &getConfig('config.cgi');
my $oldpassword = '';
my $newpassword = '';
my $database;
my $DBIgetAllEntries;
my $entryNumber = 0;


#If RuterSearch is not installed---------------------------------------------------------------------------------
if(lc $config{'installed'} ne 'true'){
	print &htmlhead('Install RuterSearch');

	#display pre-installation - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	if(not $query{'install'}){
		print <<HTMLCODE;	
			<script language="javascript" type="text/javascript">
			<!--
				function validate(form){
					if(!form.password.value){
						alert("Please enter a password that you would like to use for accessing administration...");
						form.password.focus();
					}
					else if(!form.verifypassword.value){
						alert("Please re-enter your administration password...");
						form.verifypassword.focus();	
					}
					else if(form.password.value != form.verifypassword.value){
						alert("Oops! The administration passwords you entered do not match. Please try again...");
						form.password.focus();	
					}
					else if(!form.mysqldbname.value && form.dbtype.selectedIndex == 1){
						alert("You absolutely must enter the name for the MySQL database. Without this, RuterSearch will crash. You might need to ask your system administrator for the name of your database name. If you cannot figure out what it is, you will need to use the Delimited Text Database.");
						form.mysqldbname.focus();
					}
					else if(!form.mysqlusername.value && form.dbtype.selectedIndex == 1){
						alert("Sorry, but unless you are accessing RuterSearch from the host computer, you must enter your MySQL username.");
						form.mysqlusername.focus();
					}
					else if(!form.mysqlpassword.value && form.dbtype.selectedIndex == 1){
						alert("Sorry, but unless you are accessing RuterSearch from the host computer, you must enter your MySQL password.");
						form.mysqlpassword.focus();
					}
					else if(confirm('Here you go! Installing RuterSearch...')){
						form.submit();
					}
				}
			//-->
			</script>
			<h1>Install RuterSearch</h1>
				<p>Welcome to RuterSearch. To start using RuterSearch, you need to install it. Please input the following and click "Install RuterSearch":</p>

				<form name="frmInstall" action="$ENV{'SCRIPT_NAME'}" method="post">
					<input type="hidden" name="install" value="1" />

					<h3>Administration Setup</h3>
					<ul>
						<li>Password: <input type="password" name="password" size="15" /></li>
						<li>Verify Password: <input type="password" name="verifypassword" size="15" /></li>
					</ul>
					<h3>Database Setup</h3>
					<p>RuterSearch uses a database to store searchable entries. The database can be either be a 
						simple delimited text file or a more advanced MySQL database. It's your choice. If you 
						are going to be search a large amount of entries, MySQL would be the best. If not, 
						the delimited text file database would be eaiser. Make sure you know your MySQL in
						information if you choose a MySQL database.</p>
					<ul>
						<li>Database type: <select name="dbtype">
							<option value="text">Delimited Text File</option>
							<option value="mysql">MySQL Database</option>
							</select>
						</li>
						<li>MySQL database name: <input type="text" name="mysqldbname" size="10" onfocus="if( document.frmInstall.dbtype.selectedIndex == 0 ){ this.blur(); alert('Since you have chosen to use a text database, you cannot edit the MySQL Database information.'); this.value = ''; document.frmInstall.dbtype.focus(); }" /></li>
						<li>MySQL username: <input type="text" name="mysqlusername" size="10"  onfocus="if( document.frmInstall.dbtype.selectedIndex == 0 ){ this.blur(); alert('Since you have chosen to use a text database, you cannot edit the MySQL Database information.'); this.value = ''; document.frmInstall.dbtype.focus(); }" /></li>
						<li>MySQL password: <input type="password" name="mysqlpassword" size="10"  onfocus="if( document.frmInstall.dbtype.selectedIndex == 0 ){ this.blur(); alert('Since you have chosen to use a text database, you cannot edit the MySQL Database information.'); this.value = ''; document.frmInstall.dbtype.focus(); }" /></li>
					</ul>
					<div style="font-size:16pt;"><input type="button" value="Install RuterSearch" onclick="validate(document.frmInstall)" /></div>
				</form>
HTMLCODE
	}
	#now install RuterSearch - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	else {

		my $errors = 0;

		print "<h2>Installing RuterSearch for $^O</h2>\n";

		#define files
		my @chmod666 = (
			'config.cgi',
			'queryrecord.txt',
			'databases/database.txt'
		);
		my @chmod755 = (
			'search.cgi',
			'add.cgi',
			'spider.cgi'			
		);
		my @chmod644 = (
			'documentation.html',
			'readme.txt',
			'html/add.html',
			'html/additionresults.html',
			'html/resulttemplate.html',
			'html/search.html',
			'html/searchresults.html'
		);


		print "<ul>\n";

		#setup unix/linux files
		if($^O =~ /unix|linux|freebsd/i){
			for(@chmod755){
				my $test = 1;

				#chmod the file for read/write
				$test = chmod(0755, $_);
				print qq`<li>chmod 755 for $_... <i>successful</i></li>\n` if $test;
				print qq`<li style="color:red;">chmod 755 for $_... <i>unsuccessful</i></li>\n` if not $test;
				$errors++ if not $test;

				$test = 1;

				#open the file
				$test = open(SOURCE, $_);
				print qq`<li style="color:red;">Unable to open &quot;$_&quot;"</li>\n` if not $test;
				$errors++ if not $test;
				next if not $test;

				my $source = '';
				read(SOURCE, $source, -s, 0);
				close SOURCE;

				#change the file
				my $perlpath = `which perl`;
				chomp $perlpath;
				$source =~ s{/usr/bin/perl}{$perlpath};

				#write the file
				$test = open(WRITE, ">$_");
				print qq`<li>Adding perl path ($perlpath) to header in $_... <i>successful</i></li>\n` if $test;
				print qq`<li style="color:red;">Adding perl path ($perlpath) to header in $_... <i>unsuccessful</i></li>\n` if not $test;
				print WRITE $source;
				close WRITE;

				$errors++ if not $test;
			}
			#chmod the file for read/write
			for(@chmod666){
				my $test = 1;
				$test = chmod(0666, $_);

				print qq`<li>chmod 666 for $_... <i>successful</i></li>\n` if $test;
				print qq`<li style="color:red;">chmod 666 for $_... <i>unsuccessful</i></li>\n` if not $test;
				$errors++ if not $test;
			}
			for(@chmod644){
				my $test = 1;
				$test = chmod(0644, $_);

				print qq`<li>chmod 644 for $_... <i>successful</i></li>\n` if $test;
				print qq`<li style="color:red;">chmod 644 for $_... <i>unsuccessful</i></li>\n` if not $test;
				$errors++ if not $test;
			}
		}

		my $test = 1;

		#setup MySQL table
		if(lc($query{'dbtype'}) eq 'mysql'){			#If using a MySQL database
			my $database = DBI->connect(("DBI:mysql:$query{'mysqldbname'}"), $query{'mysqlusername'}, $query{'mysqlpassword'}) or &cgidie(&errorMsg("Error: Unable to connect to MySQL database. You must have incorrectly entered the database name, username, or password."), &backButton);

			#test to see if rutersearch table exists
			my $tableTest = $database->prepare('SELECT * FROM rutersearch');
			$tableTest->execute;
			if(not DBI->errstr){
				print qq`<li>Notice: MySQL database table "rutersearch" already exists.</li>`;
			}
			#create table rutersearch
			else {
				my $test = 0;
				my $setupTable = $database->prepare("CREATE TABLE rutersearch (\n\tadddate\tCHARACTER (19)\t\tNOT NULL,\n\tentrytype\tCHARACTER (10)\t\tNOT NULL,\n\ttitle\tCHARACTER (128)\t\tNOT NULL,\n\tdescription\tCHARACTER (255),\n\turl\tCHARACTER (255)\t\tNOT NULL,\n\tkeywords\tCHARACTER (255),\n\tauthor\tCHARACTER (64)\n);");
				$setupTable->execute;
				$test = DBI->errstr;
				print qq`<li style="color:red;">Error setting up MySQL database table "rutersearch": <i>$test</i></li>\n` if $test;
				print qq`<li>MySQL database table "rutersearch" has been created.</li>\n` if not $test;
				$setupTable->finish;
			}
			$tableTest->finish;
			$database->disconnect;
		}

		#update the config file
		$config{'installed'} = 'true';
		$config{'password'} = $query{'password'};
		$config{'dbtype'} = $query{'dbtype'};
		$config{'mysqldbname'} = $query{'mysqldbname'};
		$config{'mysqlusername'} = $query{'mysqlusername'};
		$config{'mysqlpassword'} = $query{'mysqlpassword'};
		$test = &putConfig('config.cgi', %config);
		print qq`<li>Updating configuration file... <i>successful</i></li>\n` if $test;
		print qq`<li style="color:red;">Updating configuration file... <i>unsuccessful</i></li>\n` if not $test;
		$errors++ if not $test;

		print "</ul>\n";

		print "<h2>You encountered $errors errors</h2>\n";
		print "<p>Since you have encountered at least one error, RuterSearch may not work correctly.</p>" if $errors;
		print qq`<h1><a href="$ENV{'SCRIPT_NAME'}">Login to Administration</a></h1>`;
	}


	print "\t</body>\n</html>\n";
	exit;
}
elsif(not -e 'config.cgi'){
	print &errorMsg('Error: Unable to locate "config.cgi", the configuration file.');
	exit;
}




#Enter Password-----------------------------------------------------------------------------------------------------
if( not $query{'password'} or lc $query{'password'} ne lc $config{'password'} ){
	print &htmlhead('Administration Page Login');
	print <<HTMLCODE;
		<h1>Administration Login</h1>
	<form method="post" action="$ENV{'SCRIPT_NAME'}" name="frmLogin">
		<input type="hidden" name="display" value="home" />
		Password: <input type='password' name='password' size='20' value="$query{'password'}" />
		<input type='submit' value='Login' />
	</form>
	<script type="text/javascript">
	<!--
HTMLCODE

	#Print password error message
	print qq`\t\talert('"$query{'password'}" is an invalid password. Please try again...');` if exists $query{'password'} and (lc $query{'password'} ne lc $config{'password'});

	print <<HTMLCODE;

		document.frmLogin.password.focus();
	//-->
	</script>
</body>
</html>
HTMLCODE
	exit;
}



#Administration home page-----------------------------------------------------------------------------------------
elsif($query{'display'} eq 'home' or $query{'display'} eq 'Update Configuration'){
	my $updating = 1 if $query{'updating'};
	if($updating){
		for(keys %config){
			if(not grep(/\Q$_\E/, keys %query)){
				print &htmlhead("Error");
				print "<h2>Please enter all fields. <a href='javascript:history.go(-1)'>Go back</a></h2>";
				print "\t</body>\n</html>\n";
				exit;
			}
		}

		#setup MySQL table
		if(lc $query{'dbtype'} eq 'mysql'){			#If using a MySQL database
			my $database = DBI->connect(("DBI:mysql:$query{'mysqldbname'}"), $query{'mysqlusername'}, $query{'mysqlpassword'}) or &cgidie(&errorMsg("Error: Unable to connect to MySQL database. You must have incorrectly entered the database name, username, or password."), &backButton);

			#test to see if rutersearch table exists
			my $tableTest = $database->prepare('SELECT * FROM rutersearch');
			$tableTest->execute;
			if(DBI->errstr){
				my $test = 0;
				my $setupTable = $database->prepare("CREATE TABLE rutersearch (\n\tadddate\tCHARACTER (19)\t\tNOT NULL,\n\tentrytype\tCHARACTER (10)\t\tNOT NULL,\n\ttitle\tCHARACTER (128)\t\tNOT NULL,\n\tdescription\tCHARACTER (255),\n\turl\tCHARACTER (255)\t\tNOT NULL,\n\tkeywords\tCHARACTER (255),\n\tauthor\tCHARACTER (64)\n);");
				$setupTable->execute;
				&cgidie(&errorMsg('Unable to create table "rutersearch": ' . DBI->errstr), &backButton) if(DBI->errstr);
				#print qq`<p>MySQL database table "rutersearch" has been created.</p>\n` if not $test;
				$setupTable->finish;
			}
			$tableTest->finish;
			$database->disconnect;
		}

		#%config = ();
		delete $query{'verifypassword'};
	$config{'password'} = $query{'newpassword'};
	$oldpassword = $query{'password'}; delete $query{'password'};
	$newpassword = ($query{'newpassword'})?$query{'newpassword'}:$oldpassword; delete $query{'newpassword'};
		delete $query{'updating'};
		delete $query{'display'};

		foreach(keys %query){
			$config{$_} = $query{$_};
		}
		&putConfig('config.cgi', %config);

		#relogin
		&relogin if $oldpassword ne $newpassword;

		#Remove this???????????????????????????????????????????????
		%config = &getConfig('config.cgi');
	}

	#Print the administration page home
	print &htmlhead("RuterSearch Administration");
	if($updating){
		print <<'		JAVASCRIPT';
		<script type="text/javascript">
		<!--
		alert("Settings have been updated successfully.");
		//-->
		</script>
		JAVASCRIPT
	}
	print <<HTMLCODE;
		<script type="text/javascript">
		<!--

		function validate(form){
			//validate every option
			if(!form.newpassword.value){
				alert("You must enter a value for the new password...");
				form.newpassword.focus();				
			}
			else if(!form.verifypassword.value){
				alert("Please verify your new password...");
				form.verifypassword.focus();				
			}
			else if(form.newpassword.value != form.verifypassword.value){
				alert("The two passwords that you entered do not match. Please re-enter them.");
				form.newpassword.focus();
			}
			else if(!form.mysqldbname.value && form.dbtype.selectedIndex == 1){
				alert("You MUST enter the name of your MySQL database...");
				form.mysqldbname.focus();				
			}
			else if(!form.mysqlusername.value && form.dbtype.selectedIndex == 1){
				alert("Please enter your MySQL username...");
				form.mysqlusername.focus();				
			}
			else if(!form.mysqlpassword.value && form.dbtype.selectedIndex == 1){
				alert("You must enter a value for your new MySQL password...");
				form.mysqlpassword.focus();				
			}
			else {
				form.submit();
			}
		}

		//-->
		</script>


		<h1>RuterSearch Administration v1.0</h1>
		<p>Welcome to RuterSearch Administration. This acts as the control center of the RuterSearch program. 
		Almost everything that you will need to do can be done here, including: database setup, entry addition, 
		entry editing, query record viewing, and other vital tasks that you will need to make RuterSearch your own.
		</p>

		<hr />
		<p>For additional information on how to use and customize RuterSearch:</p>
		<h3><a href="javascript:void(0)" onclick="window.open('$ENV{'SCRIPT_NAME'}?display=documentation&password=$config{'password'}', 'ManageEntries', 'width=600,height=300,scrollbars=yes,resizable=yes,toolbar=no,status=no,location=no')">RuterSearch Documentation</a></h3>

		<form name="frmAdmin" method="post" action="$ENV{'SCRIPT_NAME'}">
		   <input type="hidden" name="password" value="$config{'password'}" />
		   <input type="hidden" name="updating" value="true" />
		   <input type="hidden" name="display" value="home" />

		<h2>Administration</h2>
		<ul>
			<li>New password: <input name="newpassword" type="password" size="10" value="$config{'password'}" 
			/></li>
			<li>Verify password: <input name="verifypassword" type="password" size="10" value="$config{'password'}" 
			/></li>
			<li>Admin email: <input name="email" type="text" size="20" value="$config{'email'}" /></li>
		</ul>

		<h2>Database Setup</h2>
		<ul>
			<li><span style="font-size:18pt"><a href="javascript:void(0)" onclick="window.open('$ENV{'SCRIPT_NAME'}?display=manageentries&password=$config{'password'}', 'ManageEntries', 'width=600,height=300,scrollbars=yes,resizable=yes,toolbar=no,status=no,location=no')">Manage Database Entries</a></span></li>
			<li>Database type: 
				<select name="dbtype" onchange="//dbChange(this.selectedIndex)">
					<option value="text">Text delimited file</option>
					<option value="mysql">MySQL database</option>
				</select>
				<script type="text/javascript">
				<!--
				if('$config{'dbtype'}' == 'text'){
					document.frmAdmin.dbtype.selectedIndex = 0;
				}
				else {
					document.frmAdmin.dbtype.selectedIndex = 1;
				}
				//-->
				</script>
			</li>
			<li>
				<table cellspacing="2" border="1" cellpadding="5">
				<tr><td>
					<b>Text Database Config.</b><br />
					Text Database Filename: <input type="text" name="dbfile" value="$config{'dbfile'}" size="10" /><br />
					Text Database Delimiter: <input type="text" name="delimiter" value="$config{'delimiter'}" size="6" />
				</td></tr>
				</table>
			</li>
			<li>
				<table cellspacing="2" border="1" cellpadding="5">
				<tr><td>
					<b>MySQL Database Config.</b><br />
					Note: If you do not currently have a MySQL table named "rutersearch", this program will make it for you. Just select "MySQL Database" from the list above, and enter your MySQL username and password below.
					<ul>
						<li>MySQL Database name: <input type="text" name="mysqldbname" value="$config{'mysqldbname'}" size="10" /></li>
						<li>Username: <input type="text" name="mysqlusername" value="$config{'mysqlusername'}" size="10" /></li>
						<li>Password: <input type="password" name="mysqlpassword" value="$config{'mysqlpassword'}" size="10" /></li>
				</td></tr>
				</table>	
			</li>
		</ul>
HTMLCODE

	print qq`<h2>Search Engine Config.</h2>
		<ul>
			<li><span style="font-size:18pt"><a href="javascript:void(0)" onclick="window.open('$ENV{'SCRIPT_NAME'}?display=queryrecord&password=$config{'password'}', 'QueryRecord', 'width=600,height=300,scrollbars=yes,resizable=yes,toolbar=no,status=no,location=no')">View Search History</a></span></li>
			<li>Default entry type to search for: <input type="text" size="2" name="resulttype" value="$config{'resulttype'}" /></li>
			<li>Generate navigation: <input type="radio" name="generatenav" value="true" ` . &truechecked($config{'generatenav'}) . qq` />true&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="generatenav" value="false" ` . &falsechecked($config{'generatenav'}) . qq` />false</li>
			<li>Defaultly style matched words: <input type="radio" name="stylewords" value="true" ` . &truechecked($config{'stylewords'}) . qq` />true&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="stylewords" value="false" ` . &falsechecked($config{'stylewords'}) . qq` />false</li>
			  <ul>
				<li><span style="font-size:10pt;">This defaultly highlights all matched words in the results of a search. For example: If searching for "White", in the entry "White House", the word white can be italicized or highlighted or even made to blink. You can change the style by editing the &lt;style&gt; tag in "searchresults.html". Just look for the line that says <b>.matchedWord</b>, and edit the CSS (Cascading Style Sheets) code in that block. If you do not know CSS, it is easy to learn. Pick up a book or goto W3C's <a href="http://www.w3.org/TR/REC-CSS1">official specification</a>.</span></li>
			  </ul>
			<li>Keep a search record (<a href="javascript:void(0)" onclick="window.open('$ENV{'SCRIPT_NAME'}?display=queryrecord&password=$config{'password'}', 'ManageEntries', 'width=600,height=300,scrollbars=yes,resizable=yes,toolbar=no,status=no,location=no')">Search History</a>): <input type="radio" name="queryrecord" value="true" ` . &truechecked($config{'queryrecord'}) . qq` />true&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="queryrecord" value="false" ` . &falsechecked($config{'queryrecord'}) . qq` />false</li>
			<li>Default results per page: <input type="text" size="2" name="perpage" value="$config{'perpage'}" /> enter 'all' if you want every result displayed on the first page</li>
			<li>Minimum Word size: <input type="text" name="wordsize" value="$config{'wordsize'}" size="3" /></li>
			  <ul>
				<li><span style="font-size:10pt;">The minimum word size determines whether or not a word will be matched inside of another word. For example: if the minimum word size is set to "3", performing a search of the word "see" will allow it to match "seeing". But if the minimum word size is set to "4", "see" will only match "see", and not "seeing" since "see" is less than the minimum word size.</span></li>
			  </ul>
			<li>
				<table cellspacing="0" border="1" cellpadding="5">
				<tr><td>
					<b>Value of Matched Words</b><br />
					The location (title, description, keywords, etc) where a match is made can each return a different score. If an exact match is made, that is when "word" matches case-insensitive "Word", its score will three times more than if it matched "wordville".
					<ul>
						<li>Title match score: <input type="text" name="matchtitle" value="$config{'matchtitle'}" size="2" /></li>
						<li>Description match score: <input type="text" name="matchdescription" value="$config{'matchdescription'}" size="2" /></li>
						<li>Url match score: <input type="text" name="matchurl" value="$config{'matchurl'}" size="2" /></li>
						<li>Keywords word score: <input type="text" name="matchkeywords" value="$config{'matchkeywords'}" size="2" /></li>
						<li>Author match score: <input type="text" name="matchauthor" value="$config{'matchauthor'}" size="2" /></li>
					</ul>
				</td></tr>
				</table>
			</li>
		</ul>

		<h2>Addition Page Config.</h2>
		<ul>
			<li>Restrict addition page (administration password): <input type="radio" name="restrictadd" value="true" ` . &truechecked($config{'restrictadd'}) . qq` />true&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="restrictadd" value="false" ` . &falsechecked($config{'restrictadd'}) . qq` />false</li>
		</ul>

		<h2>Webpage Spider Config.</h2>
		<ul>
			<li>Restrict website spider page (administration password): <input type="radio" name="restrictspider" value="true" ` . &truechecked($config{'restrictspider'}) . qq` />true&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="restrictspider" value="false" ` . &falsechecked($config{'restrictspider'}) . qq` />false</li>
		</ul>

	<center><input type="button" value="Update Configuration" onclick="validate(document.frmAdmin)" /></center>
		</form>


`;

		
	print "\t</body>\n</html>\n";
	exit;
}



#View the query record##############################################################################################
elsif($query{'display'} eq 'queryrecord'){
	print &htmlhead('Search History');
	print qq`\t\t<h2>Search History <span style="font-size:12pt;"><a href="javascript:void(0)" onclick="window.close()">Close Window</a></span></h2>\n`;

	#print the table
	print qq`\t\t<table cellpadding="5" cellspacing="2" border="1">\n`;
	print qq`\t\t\t<tr>\n`;
	print qq`\t\t\t\t<td><b>Date</b></td> <td><b>IP Address</b></td> <td><b>User Agent</b></td> <td><b>Type</b></td> <td><b>Search Query</b></td> <td><b>Results</b></td>\n`;
	print qq`\t\t\t</tr>\n`;

	#open the query record
	my @queryrecord = ();
	open(RECORD, 'queryrecord.txt');
	@queryrecord = reverse(<RECORD>);
	close RECORD;

	#Go through each line in the query and print it in columns
	for(@queryrecord){
		chomp;
		my($date, $ip, $useragent, $numresults, $type, $query) = split(/\t\t/, $_);
		print qq`\t\t\t\t<tr><td>$date</td> <td>$ip</td> <td>$useragent</td> <td>$type</td> <td>$query</td> <td>$numresults</td></tr>\n`;
	}

	print "\t\t</table>\n";
	print qq`<h2><a href="javascript:void(0)" onclick="window.close()">Close Window</a></h2>\n`;
	print "\n\t</body>\n</html>\n";
	exit;
}


#Manage the entries in the database###################################################################################
elsif($query{'display'} eq 'manageentries'){

	#Home page for managing entries---------------------------------------------------------------------------------
	if(not $query{'manage'}){
		print &htmlhead('Manage Entries');
		print qq`\t\t<h2>Manage Entries <span style="font-size:12pt;"><a href="javascript:void(0)" onclick="window.close()">Close Window</a></span></h2>\n`;
		print <<HTMLCODE;
			<p>Here you can add (and spider), edit, and delete entries in your database. </p>
			<ul>
				<li><big><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries&manage=add">Add an entry</a></big></li>
				<li><big><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries&manage=spider">Spider: add many entries</a></big></li>
				<li><big>Edit (coming in next major release)</big></li>
				<li><big><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries&manage=delete">Delete an entry</a></big></li>
			</ul>
HTMLCODE
		print "\n\t</body>\n</html>\n";
		exit;
	}

	#Admin add--------------------------------------------------------------------------------------------------------
	elsif(lc $query{'manage'} eq 'add'){
		print &htmlhead('Add an Entry');
		print qq`<h2>Add an Entry <span style="font-size:12pt;"><a href="javascript:void(0)" onclick="window.close()">Close Window</a></span></h2>\n`;
		print qq`<h4><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries">Manage Home</a></h4>`;

		print <<HTMLCODE;
			<p>
				You know what? There is already a addition program that comes with RuterSearch. It should be called "add.cgi", and you can access it by <a href="add.cgi?password=$query{'password'}" target="_blank">clicking here</a>.
			</p>
HTMLCODE

		print "\n\t</body>\n</html>\n";
		exit;
	}

	#Spider-----------------------------------------------------------------------------------------------------------
	elsif(lc $query{'manage'} eq 'spider'){
		print &htmlhead('Spider: Add many entries');
		print qq`<h2>Spider for many Additions <span style="font-size:12pt;"><a href="javascript:void(0)" onclick="window.close()">Close Window</a></span></h2>\n`;
		print qq`<h4><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries">Manage Home</a></h4>`;

		print <<HTMLCODE;
			<p>The spider allows the addition of all the links on a certain page. It goes through each link and parses out the title, description, keywords, and author from the specified &lt;meta&gt; tags. If no description is supplied, the spider will attempt to assemble a description from the text on the page. Please note: this spider only goes one level deep. When a url is supplied, the parser will only parse the links on that page, not on subsequent pages.</p>

			<p>Since the spider requires the use of the <i>LWP::Simple</i> module, I have placed the spider in a file called "spider.cgi". That way if you do not have that module installed, you could still access administration. If you don't have that module, the spider program will not execute. You can access the spider by <a href="spider.cgi?password=$query{'password'}" target="_blank">clicking here</a>.</p>
HTMLCODE


		print "\n\t</body>\n</html>\n";
		exit;
	}

	#Delete-----------------------------------------------------------------------------------------------------------
	elsif(lc $query{'manage'} eq 'delete'){
		print &htmlhead('Delete an Entry');
		print qq`<h2>Delete an Entry <span style="font-size:12pt;"><a href="javascript:void(0)" onclick="window.close()">Close Window</a></span></h2>\n`;
		print qq`<h4><a href="$ENV{'SCRIPT_NAME'}?password=$query{'password'}&display=manageentries">Manage Home</a></h4>`;

		#Get the all the titles
		my @titles = ();
		my @dblines = ();
		&openDatabase;
		for(my %entryFields = &getFields;   %entryFields;   %entryFields = &getFields){
			push(@titles, $entryFields{'title'}) if $entryFields{'title'} and (&trim($query{'title'}) ne &trim($entryFields{'title'}));
			push(@dblines, ($entryFields{'date'} . $config{'delimiter'} . $entryFields{'type'} . $config{'delimiter'} . $entryFields{'title'} . $config{'delimiter'} . $entryFields{'description'} . $config{'delimiter'} . $entryFields{'url'} . $config{'delimiter'} . $entryFields{'keywords'} . $config{'delimiter'} . $entryFields{'author'} . "\n")) if (&trim($query{'title'}) ne &trim($entryFields{'title'})) and (not exists $config{'dbtype'} or lc $config{'dbtype'} eq 'text') and $query{'title'} and $entryFields{'title'};
		}


		#If there is a query
		if($query{'title'}){
				if(lc $config{'dbtype'} eq 'text'){
							close DATABASE;
							open(DATABASE, '>databases/' . $config{'dbfile'});
							foreach my $line (@dblines){
								print DATABASE $line;
							}
							close DATABASE;
							
				}
				elsif(lc $config{'dbtype'} eq 'mysql'){
					my $DBIdelete;
					$DBIdelete = $database->prepare(qq`DELETE FROM rutersearch WHERE title = "$query{'title'}"`);
					$DBIdelete->execute;
					$DBIdelete->finish;
				}
				else { print "Unknown database type!" }


				print qq`<p>&quot;$query{'title'}&quot; has been deleted.</p>\n`;
		}
		&closeDatabase;

		#Print the titles, sorted in a <SELECT> box
		print qq`<form name="frmTitles" action="$ENV{'SCRIPT_NAME'}">
				<input type="hidden" name="password" value="$query{'password'}" />
				<input type="hidden" name="display" value="manageentries" />
				<input type="hidden" name="manage" value="delete" />
				<select name="title">\n`;
		foreach $_ (sort {lc $a cmp lc $b} @titles){ print qq`<option>$_</option>\n`; }
		print qq`</select><br /><input type="submit" value="Delete Entry" /></form>`;

		print "\n\t</body>\n</html>\n";
		exit;
	}

	else {
		print "Error: Unknown manage.";
	}
	exit;
}

#Display the documentation-----------------------------------------------------------------------------------------
elsif(lc $query{'display'} eq 'documentation'){
	open(DOCUMENTATION, 'documentation.html') or &cgidie( &errorMsg('Error: Unable to find "documentation.html".') );
	my $source = '';
	read(DOCUMENTATION, $source, -s 'documentation.html', 0);
	print $source;
	close DOCUMENTATION;
	exit;
}
else {
	print qq`<a href="$ENV{'SCRIPT_NAME'}">Administration</a>`;
}








#Subroutines-------------------------------------------------------------------------------------------------------------
sub htmlhead {
	return <<HTMLCODE;
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
	<head>
		<title>$_[0]</title>
		<style type="text/css">
			body,td,h1,h2,h3,h4,p,ul,ol,li,input {
				font-family:Veranda,Arial,Helvetica,Serif;
			}
		</style>
	</head>
	<body>
HTMLCODE
}

sub htmldtd {
	my $request = shift;
	if('transitional' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	elsif('strict' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	elsif('frameset' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	else {
		return &errorMsg("Wrong DTD");
	}
}

sub htmlfoot {
	return "\n</html>\n" . 
	'';
}

sub trim {
	my $string = shift;
	return $string if not $string;	
	$string =~ s/\s+/ /g;
	$string =~ s/^ //;
	$string =~ s/ $//;
	return $string;
}

sub backButton {
	return("<br><div align=\"center\" style=\"font-size:20pt; \"><a href=\"javascript:history.go(-1)\">&lt; Go Back</a></div>");
}

sub errorMsg {
	return("<div align=\"center\" style=\"color:red; font-weight:bold;\">$_[0]</div>");
}

sub reportError {
	#$_[0] is the error code
	return("<div align=\"center\" style=\"font-size:20pt; \">Report error to <a href=\"mailto:$config{'email'}?subject=Error code $_[0]\">search administrator</a></div>");
}

sub readQuery {
	my $string = '';
	if($ARGV[0]) {
		$string = $ARGV[0];
	}
	elsif($ENV{'REQUEST_METHOD'} eq 'GET'){	#method='get'
		$string = $ENV{'QUERY_STRING'};
	}
	elsif($ENV{'REQUEST_METHOD'} eq 'POST') {
		read(STDIN, $string, $ENV{'CONTENT_LENGTH'});	#method='post'
	}
	return $string;
}

sub httpQueryVars {
	#Either "text", "html", "urlencoded", or none
	my $query = pop @_;
	my $type = lc pop(@_);
	my $pair = '';
	my(%query,%hexQuery,%htmlQuery) = ();

	#$query =~ s/%0D%0A/\n/gi;

	#Parse and set the query variables into %query and %hexQuery
	foreach $pair (split(/&/, $query)){				#Cycle through each value pairs
		my($key, $value) = split(/=/, $pair);		#Separate name and value
		$key =~ tr/+/ /;
		$key =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		$hexQuery{lc($key)} = $value;	  	#Assign URL encoded variable to a %hexQuery variable
		next if $type eq 'urlencoded';
		$value =~ tr/+/ /;
		$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		$query{lc($key)} = $value;		#Assign name and varible to a hash variable
		next if $type eq 'text';
		$htmlQuery{lc($key)} = scalar &htmlEntities($value);
	}

	return %query if $type eq "text";
	return %hexQuery if $type eq "urlencoded";
	return %htmlQuery if $type eq "html";
}

sub htmlEntities {
	my(@array) = ();
	my(@items) = @_;

	for(@items){
		s/&/&amp;/g;
		s/"/&quot;/g;
		s/'/&#39;/g;
		s/</&lt;/g;
		s/>/&gt;/g;
		push(@array, $_);
	}

	return @array if(scalar(@items) > 1);
	return $array[0] if(scalar(@items) == 1);
}

sub getConfig {
	my %config = ();
	local *FILE;

	if(not(-e($_[0]))){
			&cgidie( &errorMsg(qq`Error: $_[0] not found.`) );
	}
	elsif(not open(FILE, $_[0])){
		return ('installed' => 'false');
	}
	else {
		for(<FILE>){
			chomp;
			my @parts = split(/=/, $_, 2);
			next if not $parts[0];
			$config{lc $parts[0]} = $parts[1];
		}
		close FILE;
		return %config;
	}
}

sub putConfig {
	my $file = shift(@_);
	my %config = @_;
	my $flockwork = 1;
	local *CONFIG;

	open(CONFIG, ">$file") or &cgidie( &errorMsg("Error: Could not write to $file.") );
	$flockwork = 0 if not eval { flock(CONFIG, 2); 1; };
	while(my($key, $value) = each(%config)){
		print CONFIG "$key=$value\n";
	}
	flock(CONFIG, 8) if $flockwork;
	close(CONFIG);

}


sub openDatabase {
	if(lc($config{'dbtype'}) eq 'text') {		#If using a text database
		if(not -e "databases/$config{'dbfile'}"){
			&cgidie( &errorMsg("Error code 001: The $config{'dbtype'} database file 'databases/$config{'dbfile'}' cannot be found."), &reportError("001"), &backButton );
		}
		open(DATABASE, "databases/$config{'dbfile'}") or &cgidie(&errorMsg("Error: Unable to open the database."), &reportError("001"), &backButton);
		my $buffer = '';
		while(sysread DATABASE, $buffer, 4096){
			$entryNumber += ($buffer =~ tr/\n//);
		}
		close DATABASE;

		open(DATABASE, "databases/$config{'dbfile'}"); 
	}
	elsif(lc($config{'dbtype'}) eq 'mysql'){			#If using a MySQL database
		$database = DBI->connect(("DBI:mysql:$config{'mysqldbname'}"), $config{'mysqlusername'}, $config{'mysqlpassword'}) or &cgidie(&errorMsg("Error: Unable to connect to MySQL database.", &reportError(), &backButton));

		#Prepare statement to get each row containing array entries
		$DBIgetAllEntries = $database->prepare("SELECT * FROM rutersearch") or return 0;
		$DBIgetAllEntries->execute;
		$entryNumber = $DBIgetAllEntries->rows;
		&cgidie(&errorMsg("Error: The MySQL database has not been set up correctly."), &backButton) if $entryNumber < 0;
	}
	else {
			&cgidie( &errorMsg("Error code 002: Unknown database type. Must be set to 'MySQL' or 'text'."), &reportError("002"), &backButton );
	}
}

sub getFields {
	my $entryNumber = shift @_;
	my %fields = ();
	my($date, $type, $title, $description, $url, $keywords, $author) = ();
	my $textDBline = '';

	if(lc $config{'dbtype'} eq 'text'){
		$textDBline = <DATABASE>;
		return %fields if not $textDBline;
		chomp $textDBline;
		($date, $type, $title, $description, $url, $keywords, $author) = split(/$config{'delimiter'}/, $textDBline, 7);
	}
	elsif(lc $config{'dbtype'} eq 'mysql'){
		($date, $type, $title, $description, $url, $keywords, $author) = $DBIgetAllEntries->fetchrow_array;
		return %fields if $DBIgetAllEntries->errstr;
	}

	%fields = (
		'date' => $date,
		'type' => $type,
		'title' => $title,
		'description' => $description,
		'url' => $url,
		'keywords' => $keywords,
		'author' => $author,
	);
	return %fields;
}

sub closeDatabase {
	if(lc($config{'dbtype'}) eq 'text'){
		close DATABASE;
	}
	elsif(lc($config{'dbtype'}) eq 'mysql'){
		$DBIgetAllEntries->finish;
		$database->disconnect;
	}
}

sub truechecked {
	if(shift eq 'true'){
		return(' checked="checked" ');
	}
}

sub falsechecked {
	my $checked = shift;
	if($checked eq 'false' or not $checked){
		return(' checked="checked" ');
	}
}

sub relogin {
	print &htmlhead('RuterSearch Administration');
	print <<HTMLCODE;
		<script type="text/javascript">
		<!--
			alert('Successful configuration change. Please re-login...')
		//-->
		</script>
		<h1>RuterSearch Administration</h1>
		<form method='post' action='admin.cgi'>
			<input type="hidden" name="display" value="home" />
			Password: <input type='password' name='password' size='20' />
			<input type='submit' value='Login' />
		</form>
	</body>
</html>
HTMLCODE
	exit;
}

sub cgidie {
	print join('', @_);
	exit;
	#return ((wantarray)? ('installed' => 'false')) : 0;
}
