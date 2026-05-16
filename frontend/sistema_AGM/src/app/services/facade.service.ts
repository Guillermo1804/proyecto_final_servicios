import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ErrorsService } from './tools/errors.service';
import { ValidatorService } from './tools/validator.service';

import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};

@Injectable({
  providedIn: 'root'
})
export class FacadeService {
  constructor(
    private http: HttpClient,
    public router: Router,

    private validatorService: ValidatorService,
    private errorService: ErrorsService,
  ) { }
  //Funcion para validar login
  public validarLogin(username: String, password: String){
    var data = {
      "username": username,
      "password": password
    }
    console.log("Validando login... ", data);
    let error: any = [];
    if(!this.validatorService.required(data["username"])){
      error["username"] = this.errorService.required;
    }else if(!this.validatorService.max(data["username"], 40)){
      error["username"] = this.errorService.max(40);
    }else if (!this.validatorService.email(data['username'])) {
      error['username'] = this.errorService.email;
    }
    if(!this.validatorService.required(data["password"])){
      error["password"] = this.errorService.required;
    }
    return error;
  }
  // Funciones básicas
  //Iniciar sesión
  public login(username:String, password:String): Observable<any> {
    var data={
      username: username,
      password: password
    }
    return this.http.post<any>(`${environment.url_api}/token/`,data, httpOptions);
  }
  //Cerrar sesión
  // public logout(): Observable<any> {
  //   var headers: any;
  //   var token = this.getSessionToken();
  //   headers = new HttpHeaders({ 'Content-Type': 'application/json' , 'Authorization': 'Bearer '+token});
  //   return this.http.get<any>(`${environment.url_api}/logout/`, {headers: headers});
  // }
  // //Funciones para utilizar las cookies en web
  // retrieveSignedUser(){
  //   var headers: any;
  //   var token = this.getSessionToken();
  //   headers = new HttpHeaders({'Authorization': 'Bearer '+token});
  //   return this.http.get<any>(`${environment.url_api}/me/`,{headers:headers});
  // }

}